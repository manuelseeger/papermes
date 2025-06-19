package com.papermes.documentscanner.utils

import android.content.Context
import android.content.SharedPreferences
import androidx.preference.PreferenceManager

class PreferencesManager(context: Context) {
    
    private val preferences: SharedPreferences = PreferenceManager.getDefaultSharedPreferences(context)
    
    companion object {
        private const val KEY_API_ENDPOINT = "api_endpoint"
        private const val KEY_API_TOKEN = "api_token"
        private const val KEY_WIFI_ONLY = "wifi_only"
        private const val KEY_DOCUMENT_CONFIDENCE_THRESHOLD = "document_confidence_threshold"
        private const val KEY_SCAN_INTERVAL = "scan_interval"
        private const val KEY_ENABLED = "enabled"
        private const val KEY_LAST_SCAN_TIME = "last_scan_time"
        
        // Default values
        private const val DEFAULT_ENDPOINT = "http://localhost:8000/api/documents/"
        private const val DEFAULT_WIFI_ONLY = true
        private const val DEFAULT_CONFIDENCE_THRESHOLD = 0.7f
        private const val DEFAULT_SCAN_INTERVAL = 30L // seconds
        private const val DEFAULT_ENABLED = true
    }
    
    var apiEndpoint: String
        get() = preferences.getString(KEY_API_ENDPOINT, DEFAULT_ENDPOINT) ?: DEFAULT_ENDPOINT
        set(value) = preferences.edit().putString(KEY_API_ENDPOINT, value).apply()
    
    var apiToken: String?
        get() = preferences.getString(KEY_API_TOKEN, null)
        set(value) = preferences.edit().putString(KEY_API_TOKEN, value).apply()
    
    var wifiOnly: Boolean
        get() = preferences.getBoolean(KEY_WIFI_ONLY, DEFAULT_WIFI_ONLY)
        set(value) = preferences.edit().putBoolean(KEY_WIFI_ONLY, value).apply()
    
    var documentConfidenceThreshold: Float
        get() = preferences.getFloat(KEY_DOCUMENT_CONFIDENCE_THRESHOLD, DEFAULT_CONFIDENCE_THRESHOLD)
        set(value) = preferences.edit().putFloat(KEY_DOCUMENT_CONFIDENCE_THRESHOLD, value).apply()
    
    var scanInterval: Long
        get() = preferences.getLong(KEY_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        set(value) = preferences.edit().putLong(KEY_SCAN_INTERVAL, value).apply()
    
    var isEnabled: Boolean
        get() = preferences.getBoolean(KEY_ENABLED, DEFAULT_ENABLED)
        set(value) = preferences.edit().putBoolean(KEY_ENABLED, value).apply()
    
    var lastScanTime: Long
        get() = preferences.getLong(KEY_LAST_SCAN_TIME, 0L)
        set(value) = preferences.edit().putLong(KEY_LAST_SCAN_TIME, value).apply()
    
    fun reset() {
        preferences.edit().clear().apply()
    }
}
