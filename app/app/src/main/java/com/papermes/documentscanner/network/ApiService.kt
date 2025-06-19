package com.papermes.documentscanner.network

import android.content.Context
import android.util.Log
import com.papermes.documentscanner.data.DocumentEntity
import com.papermes.documentscanner.utils.PreferencesManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.logging.HttpLoggingInterceptor
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiService(private val context: Context) {
    
    companion object {
        private const val TAG = "ApiService"
        private const val CONNECT_TIMEOUT = 30L
        private const val READ_TIMEOUT = 60L
        private const val WRITE_TIMEOUT = 60L
    }
    
    private val preferencesManager = PreferencesManager(context)
    
    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(CONNECT_TIMEOUT, TimeUnit.SECONDS)
        .readTimeout(READ_TIMEOUT, TimeUnit.SECONDS)
        .writeTimeout(WRITE_TIMEOUT, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .build()
    
    data class UploadResponse(
        val success: Boolean,
        val message: String,
        val documentId: String? = null
    )
    
    suspend fun uploadDocument(document: DocumentEntity): UploadResponse = withContext(Dispatchers.IO) {
        try {
            val endpoint = preferencesManager.apiEndpoint
            val token = preferencesManager.apiToken
            
            if (endpoint.isBlank()) {
                return@withContext UploadResponse(false, "API endpoint not configured")
            }
            
            // Copy the file to a temporary location so we can access it
            val sourceFile = File(document.filePath)
            if (!sourceFile.exists()) {
                return@withContext UploadResponse(false, "Source file does not exist: ${document.filePath}")
            }
            
            val tempFile = File(context.cacheDir, "temp_${document.id}.${getFileExtension(document.fileName)}")
            sourceFile.copyTo(tempFile, overwrite = true)
            
            try {
                val mediaType = document.mimeType.toMediaTypeOrNull()
                val fileRequestBody = tempFile.asRequestBody(mediaType)
                
                val multipartBuilder = MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart(
                        "document",
                        document.fileName,
                        fileRequestBody
                    )
                    .addFormDataPart("filename", document.fileName)
                    .addFormDataPart("mime_type", document.mimeType)
                    .addFormDataPart("size", document.size.toString())
                    .addFormDataPart("width", document.width.toString())
                    .addFormDataPart("height", document.height.toString())
                    .addFormDataPart("date_added", document.dateAdded.time.toString())
                    .addFormDataPart("date_modified", document.dateModified.time.toString())
                    .addFormDataPart("confidence", document.confidence.toString())
                
                val requestBuilder = Request.Builder()
                    .url(endpoint)
                    .post(multipartBuilder.build())
                
                // Add authorization header if token is provided
                if (!token.isNullOrBlank()) {
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
                
                val request = requestBuilder.build()
                
                Log.d(TAG, "Uploading document: ${document.fileName} to $endpoint")
                
                val response = httpClient.newCall(request).execute()
                
                response.use {
                    val responseBody = it.body?.string() ?: ""
                    
                    if (it.isSuccessful) {
                        Log.i(TAG, "Successfully uploaded document: ${document.fileName}")
                        UploadResponse(true, "Upload successful", document.id)
                    } else {
                        val errorMessage = "Upload failed: HTTP ${it.code} - $responseBody"
                        Log.e(TAG, errorMessage)
                        UploadResponse(false, errorMessage)
                    }
                }
            } finally {
                // Clean up temp file
                if (tempFile.exists()) {
                    tempFile.delete()
                }
            }
            
        } catch (e: IOException) {
            val errorMessage = "Network error: ${e.message}"
            Log.e(TAG, errorMessage, e)
            UploadResponse(false, errorMessage)
        } catch (e: Exception) {
            val errorMessage = "Upload error: ${e.message}"
            Log.e(TAG, errorMessage, e)
            UploadResponse(false, errorMessage)
        }
    }
    
    private fun getFileExtension(fileName: String): String {
        return fileName.substringAfterLast('.', "")
    }
    
    suspend fun testConnection(): UploadResponse = withContext(Dispatchers.IO) {
        try {
            val endpoint = preferencesManager.apiEndpoint
            val token = preferencesManager.apiToken
            
            if (endpoint.isBlank()) {
                return@withContext UploadResponse(false, "API endpoint not configured")
            }
            
            // Try to make a simple GET request to test connectivity
            val testUrl = if (endpoint.endsWith("/")) {
                "${endpoint}health"
            } else {
                "$endpoint/health"
            }
            
            val requestBuilder = Request.Builder()
                .url(testUrl)
                .get()
            
            if (!token.isNullOrBlank()) {
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }
            
            val request = requestBuilder.build()
            val response = httpClient.newCall(request).execute()
            
            response.use {
                if (it.isSuccessful) {
                    UploadResponse(true, "Connection successful")
                } else {
                    UploadResponse(false, "Connection failed: HTTP ${it.code}")
                }
            }
        } catch (e: Exception) {
            val errorMessage = "Connection test failed: ${e.message}"
            Log.e(TAG, errorMessage, e)
            UploadResponse(false, errorMessage)
        }
    }
}
