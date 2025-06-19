package com.papermes.documentscanner.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.preference.EditTextPreference
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.SwitchPreferenceCompat
import com.papermes.documentscanner.DocumentScannerApplication
import com.papermes.documentscanner.R
import com.papermes.documentscanner.network.ApiService
import com.papermes.documentscanner.service.DocumentScannerService
import com.papermes.documentscanner.utils.PermissionUtils
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        if (savedInstanceState == null) {
            supportFragmentManager
                .beginTransaction()
                .replace(R.id.settings, SettingsFragment())
                .commit()
        }
        
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Document Scanner Settings"
    }
    
    class SettingsFragment : PreferenceFragmentCompat() {
        
        private lateinit var app: DocumentScannerApplication
        private lateinit var apiService: ApiService
        
        private val requestPermissionLauncher = registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->
            val allGranted = permissions.values.all { it }
            if (allGranted) {
                enableService()
            } else {
                showPermissionDeniedDialog()
            }
        }
        
        override fun onCreate(savedInstanceState: Bundle?) {
            super.onCreate(savedInstanceState)
            app = requireActivity().application as DocumentScannerApplication
            apiService = ApiService(requireContext())
        }
        
        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            setPreferencesFromResource(R.xml.preferences, rootKey)
            
            setupPreferences()
        }
        
        private fun setupPreferences() {
            // Service enabled switch
            findPreference<SwitchPreferenceCompat>("enabled")?.apply {
                setOnPreferenceChangeListener { _, newValue ->
                    val enabled = newValue as Boolean
                    if (enabled) {
                        if (PermissionUtils.hasRequiredPermissions(requireContext())) {
                            enableService()
                        } else {
                            requestPermissions()
                            false // Don't change the preference until permissions are granted
                        }
                    } else {
                        disableService()
                    }
                    true
                }
            }
            
            // API Endpoint
            findPreference<EditTextPreference>("api_endpoint")?.apply {
                summaryProvider = EditTextPreference.SimpleSummaryProvider.getInstance()
            }
            
            // API Token
            findPreference<EditTextPreference>("api_token")?.apply {
                summaryProvider = Preference.SummaryProvider<EditTextPreference> { preference ->
                    if (preference.text.isNullOrBlank()) {
                        "Not set"
                    } else {
                        "••••••••"
                    }
                }
            }
            
            // Test Connection
            findPreference<Preference>("test_connection")?.apply {
                setOnPreferenceClickListener {
                    testApiConnection()
                    true
                }
            }
            
            // Document Count
            findPreference<Preference>("document_count")?.apply {
                lifecycleScope.launch {
                    val count = app.repository.getDocumentCount()
                    summary = "$count documents detected"
                }
            }
            
            // Open App Settings
            findPreference<Preference>("app_settings")?.apply {
                setOnPreferenceClickListener {
                    openAppSettings()
                    true
                }
            }
        }
        
        private fun requestPermissions() {
            val permissions = PermissionUtils.getRequiredPermissions()
            requestPermissionLauncher.launch(permissions)
        }
        
        private fun enableService() {
            DocumentScannerService.startService(requireContext())
            Toast.makeText(requireContext(), "Document Scanner enabled", Toast.LENGTH_SHORT).show()
        }
        
        private fun disableService() {
            DocumentScannerService.stopService(requireContext())
            Toast.makeText(requireContext(), "Document Scanner disabled", Toast.LENGTH_SHORT).show()
        }
        
        private fun showPermissionDeniedDialog() {
            AlertDialog.Builder(requireContext())
                .setTitle("Permissions Required")
                .setMessage("Document Scanner needs access to your photos and notification permissions to work properly.")
                .setPositiveButton("Settings") { _, _ ->
                    openAppSettings()
                }
                .setNegativeButton("Cancel", null)
                .show()
        }
        
        private fun openAppSettings() {
            val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
                data = Uri.fromParts("package", requireContext().packageName, null)
            }
            startActivity(intent)
        }
        
        private fun testApiConnection() {
            lifecycleScope.launch {
                try {
                    val result = apiService.testConnection()
                    if (result.success) {
                        Toast.makeText(requireContext(), "Connection successful!", Toast.LENGTH_LONG).show()
                    } else {
                        Toast.makeText(requireContext(), "Connection failed: ${result.message}", Toast.LENGTH_LONG).show()
                    }
                } catch (e: Exception) {
                    Toast.makeText(requireContext(), "Connection error: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
