package com.papermes.documentscanner.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.papermes.documentscanner.service.DocumentScannerService
import com.papermes.documentscanner.utils.PreferencesManager

class BootReceiver : BroadcastReceiver() {
    
    companion object {
        private const val TAG = "BootReceiver"
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        Log.d(TAG, "Received broadcast: ${intent.action}")
        
        when (intent.action) {
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_MY_PACKAGE_REPLACED,
            Intent.ACTION_PACKAGE_REPLACED -> {
                val preferencesManager = PreferencesManager(context)
                
                if (preferencesManager.isEnabled) {
                    Log.i(TAG, "Starting Document Scanner Service after boot/update")
                    DocumentScannerService.startService(context)
                } else {
                    Log.i(TAG, "Document Scanner Service is disabled, not starting")
                }
            }
        }
    }
}
