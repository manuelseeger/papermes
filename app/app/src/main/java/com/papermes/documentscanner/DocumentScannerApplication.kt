package com.papermes.documentscanner

import android.app.Application
import androidx.work.Configuration
import androidx.work.WorkManager
import com.papermes.documentscanner.data.AppDatabase
import com.papermes.documentscanner.repository.DocumentRepository
import com.papermes.documentscanner.service.DocumentScannerService
import com.papermes.documentscanner.utils.PreferencesManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class DocumentScannerApplication : Application(), Configuration.Provider {
    
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    
    // Database
    val database by lazy { AppDatabase.getDatabase(this) }
    
    // Repository
    val repository by lazy { DocumentRepository(database.documentDao()) }
    
    // Preferences
    val preferencesManager by lazy { PreferencesManager(this) }
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize WorkManager
        WorkManager.initialize(this, workManagerConfiguration)
        
        // Start the background service
        DocumentScannerService.startService(this)
    }
    
    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(android.util.Log.INFO)
            .build()
}
