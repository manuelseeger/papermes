package com.papermes.documentscanner.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.papermes.documentscanner.DocumentScannerApplication
import com.papermes.documentscanner.R
import com.papermes.documentscanner.ml.DocumentDetector
import com.papermes.documentscanner.network.ApiService
import com.papermes.documentscanner.ui.MainActivity
import com.papermes.documentscanner.utils.MediaScanner
import com.papermes.documentscanner.utils.NetworkUtils
import com.papermes.documentscanner.utils.PermissionUtils
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.Date

class DocumentScannerService : LifecycleService() {
    
    companion object {
        private const val TAG = "DocumentScannerService"
        private const val NOTIFICATION_ID = 1
        private const val CHANNEL_ID = "document_scanner_channel"
        private const val CHANNEL_NAME = "Document Scanner"
        
        fun startService(context: Context) {
            val intent = Intent(context, DocumentScannerService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stopService(context: Context) {
            val intent = Intent(context, DocumentScannerService::class.java)
            context.stopService(intent)
        }
    }
    
    private lateinit var app: DocumentScannerApplication
    private lateinit var mediaScanner: MediaScanner
    private lateinit var documentDetector: DocumentDetector
    private lateinit var apiService: ApiService
    private lateinit var networkUtils: NetworkUtils
    private lateinit var notificationManager: NotificationManager
    
    private var isScanning = false
    private var documentsProcessed = 0
    private var documentsSent = 0
    
    override fun onCreate() {
        super.onCreate()
        
        app = application as DocumentScannerApplication
        mediaScanner = MediaScanner(this)
        documentDetector = DocumentDetector(this)
        apiService = ApiService(this)
        networkUtils = NetworkUtils(this)
        notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, createNotification())
        
        Log.i(TAG, "Document Scanner Service created")
        startBackgroundWork()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        
        if (!app.preferencesManager.isEnabled) {
            Log.i(TAG, "Service is disabled, stopping...")
            stopSelf()
            return START_NOT_STICKY
        }
        
        return START_STICKY
    }
    
    override fun onBind(intent: Intent): IBinder? {
        super.onBind(intent)
        return null
    }
    
    override fun onDestroy() {
        super.onDestroy()
        documentDetector.cleanup()
        Log.i(TAG, "Document Scanner Service destroyed")
    }
    
    private fun startBackgroundWork() {
        lifecycleScope.launch {
            while (isActive && app.preferencesManager.isEnabled) {
                try {
                    if (PermissionUtils.hasRequiredPermissions(this@DocumentScannerService)) {
                        performScan()
                        processDocuments()
                        uploadDocuments()
                        cleanupOldData()
                    } else {
                        Log.w(TAG, "Missing required permissions")
                    }
                    
                    // Wait for the configured interval before next scan
                    val scanInterval = app.preferencesManager.scanInterval * 1000 // Convert to milliseconds
                    delay(scanInterval)
                    
                } catch (e: Exception) {
                    Log.e(TAG, "Error in background work", e)
                    delay(30000) // Wait 30 seconds before retrying
                }
            }
        }
    }
    
    private suspend fun performScan() {
        if (isScanning) {
            Log.d(TAG, "Scan already in progress, skipping...")
            return
        }
        
        isScanning = true
        updateNotification("Scanning for new images...")
        
        try {
            val lastScanTime = app.preferencesManager.lastScanTime
            val newImages = mediaScanner.scanForNewImages(lastScanTime)
            
            if (newImages.isNotEmpty()) {
                Log.i(TAG, "Found ${newImages.size} new images")
                app.repository.insertDocuments(newImages)
            }
            
            app.preferencesManager.lastScanTime = System.currentTimeMillis()
            
        } catch (e: Exception) {
            Log.e(TAG, "Error during scan", e)
        } finally {
            isScanning = false
        }
    }
    
    private suspend fun processDocuments() {
        updateNotification("Processing documents...")
        
        try {
            app.repository.getUnprocessedDocuments().collect { unprocessedDocs ->
                if (unprocessedDocs.isEmpty()) return@collect
                
                Log.i(TAG, "Processing ${unprocessedDocs.size} unprocessed documents")
                
                for (document in unprocessedDocs) {
                    try {
                        val imageUri = mediaScanner.getImageUri(document.id)
                        val result = documentDetector.detectDocument(imageUri)
                        
                        app.repository.updateDocumentProcessingResult(
                            document.id,
                            result.isDocument,
                            result.confidence
                        )
                        
                        if (result.isDocument) {
                            documentsProcessed++
                            Log.i(TAG, "Document detected: ${document.fileName} (confidence: ${result.confidence})")
                        }
                        
                    } catch (e: Exception) {
                        Log.e(TAG, "Error processing document ${document.fileName}", e)
                        // Mark as processed even if there was an error to avoid reprocessing
                        app.repository.updateDocumentProcessingResult(document.id, false, 0f)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error processing documents", e)
        }
    }
    
    private suspend fun uploadDocuments() {
        if (!networkUtils.shouldUpload(app.preferencesManager.wifiOnly)) {
            Log.d(TAG, "Upload conditions not met (network: ${networkUtils.getNetworkType()}, wifi only: ${app.preferencesManager.wifiOnly})")
            return
        }
        
        updateNotification("Uploading documents...")
        
        try {
            app.repository.getUnsyncedDocuments().collect { unsyncedDocs ->
                if (unsyncedDocs.isEmpty()) return@collect
                
                Log.i(TAG, "Uploading ${unsyncedDocs.size} unsynced documents")
                
                for (document in unsyncedDocs) {
                    try {
                        val result = apiService.uploadDocument(document)
                        
                        if (result.success) {
                            app.repository.markDocumentAsSent(document.id)
                            documentsSent++
                            Log.i(TAG, "Successfully uploaded: ${document.fileName}")
                        } else {
                            val retryCount = document.retryCount + 1
                            app.repository.updateDocumentRetry(
                                document.id,
                                retryCount,
                                Date(),
                                result.message
                            )
                            Log.w(TAG, "Failed to upload ${document.fileName}: ${result.message}")
                        }
                        
                    } catch (e: Exception) {
                        Log.e(TAG, "Error uploading document ${document.fileName}", e)
                        val retryCount = document.retryCount + 1
                        app.repository.updateDocumentRetry(
                            document.id,
                            retryCount,
                            Date(),
                            e.message
                        )
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error uploading documents", e)
        }
    }
    
    private suspend fun cleanupOldData() {
        try {
            // Clean up documents older than 30 days
            val cutoffDate = Date(System.currentTimeMillis() - (30 * 24 * 60 * 60 * 1000L))
            app.repository.deleteOldDocuments(cutoffDate)
        } catch (e: Exception) {
            Log.e(TAG, "Error cleaning up old data", e)
        }
    }
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Document Scanner background service"
                setShowBadge(false)
            }
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(contentText: String = "Monitoring for new documents"): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Document Scanner")
            .setContentText(contentText)
            .setSmallIcon(R.drawable.ic_document)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setAutoCancel(false)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }
    
    private fun updateNotification(contentText: String) {
        val notification = createNotification(contentText)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}
