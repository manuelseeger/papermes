package com.papermes.documentscanner.ml

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Log
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions
import com.google.mlkit.vision.documentscanner.GmsDocumentScanning
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import java.io.InputStream
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class DocumentDetector(private val context: Context) {
    
    companion object {
        private const val TAG = "DocumentDetector"
        private const val MIN_TEXT_LENGTH = 10
        private const val MIN_CONFIDENCE = 0.5f
    }
    
    private val textRecognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    
    data class DocumentDetectionResult(
        val isDocument: Boolean,
        val confidence: Float,
        val textLength: Int = 0,
        val hasStructuredContent: Boolean = false
    )
    
    suspend fun detectDocument(imageUri: Uri): DocumentDetectionResult {
        return try {
            val bitmap = loadBitmapFromUri(imageUri)
            if (bitmap == null) {
                Log.w(TAG, "Failed to load bitmap from URI: $imageUri")
                return DocumentDetectionResult(false, 0f)
            }
            
            analyzeImageForDocument(bitmap)
        } catch (e: Exception) {
            Log.e(TAG, "Error detecting document", e)
            DocumentDetectionResult(false, 0f)
        }
    }
    
    private fun loadBitmapFromUri(uri: Uri): Bitmap? {
        return try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            inputStream?.use { stream ->
                // First, get the dimensions without loading the full image
                val options = BitmapFactory.Options().apply {
                    inJustDecodeBounds = true
                }
                BitmapFactory.decodeStream(stream, null, options)
                
                // Calculate sample size to reduce memory usage
                val sampleSize = calculateSampleSize(options.outWidth, options.outHeight, 1024, 1024)
                
                // Now load the bitmap with the calculated sample size
                val inputStream2: InputStream? = context.contentResolver.openInputStream(uri)
                inputStream2?.use { stream2 ->
                    val loadOptions = BitmapFactory.Options().apply {
                        inSampleSize = sampleSize
                        inJustDecodeBounds = false
                    }
                    BitmapFactory.decodeStream(stream2, null, loadOptions)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading bitmap", e)
            null
        }
    }
    
    private fun calculateSampleSize(width: Int, height: Int, reqWidth: Int, reqHeight: Int): Int {
        var inSampleSize = 1
        if (height > reqHeight || width > reqWidth) {
            val halfHeight = height / 2
            val halfWidth = width / 2
            while ((halfHeight / inSampleSize) >= reqHeight && (halfWidth / inSampleSize) >= reqWidth) {
                inSampleSize *= 2
            }
        }
        return inSampleSize
    }
    
    private suspend fun analyzeImageForDocument(bitmap: Bitmap): DocumentDetectionResult {
        return suspendCancellableCoroutine { continuation ->
            val image = InputImage.fromBitmap(bitmap, 0)
            
            textRecognizer.process(image)
                .addOnSuccessListener { visionText ->
                    val textLength = visionText.text.length
                    val hasStructuredContent = detectStructuredContent(visionText.text)
                    
                    // Calculate confidence based on various factors
                    val confidence = calculateDocumentConfidence(
                        textLength = textLength,
                        hasStructuredContent = hasStructuredContent,
                        imageAspectRatio = bitmap.width.toFloat() / bitmap.height.toFloat(),
                        textBlocks = visionText.textBlocks.size
                    )
                    
                    val isDocument = confidence >= MIN_CONFIDENCE && textLength >= MIN_TEXT_LENGTH
                    
                    Log.d(TAG, "Document analysis - Text length: $textLength, Confidence: $confidence, IsDocument: $isDocument")
                    
                    val result = DocumentDetectionResult(
                        isDocument = isDocument,
                        confidence = confidence,
                        textLength = textLength,
                        hasStructuredContent = hasStructuredContent
                    )
                    
                    continuation.resume(result)
                }
                .addOnFailureListener { exception ->
                    Log.e(TAG, "Text recognition failed", exception)
                    continuation.resumeWithException(exception)
                }
        }
    }
    
    private fun detectStructuredContent(text: String): Boolean {
        val documentPatterns = listOf(
            // Common document patterns
            Regex("\\b\\d{1,2}[/.\\-]\\d{1,2}[/.\\-]\\d{2,4}\\b"), // Dates
            Regex("\\$\\d+(\\.\\d{2})?"), // Currency
            Regex("\\b[A-Z]{2,}\\s+[A-Z]{2,}\\b"), // All caps words (headers)
            Regex("\\b(Invoice|Receipt|Bill|Statement|Contract|Agreement|Certificate|License)\\b", RegexOption.IGNORE_CASE),
            Regex("\\b\\d{3,}\\b"), // Numbers (could be amounts, phone numbers, etc.)
            Regex("^\\s*[\\d.]+\\s*$", RegexOption.MULTILINE), // Lines with only numbers
            Regex("\\b[A-Z][a-z]+\\s*:"), // Labels followed by colon
        )
        
        var matches = 0
        for (pattern in documentPatterns) {
            if (pattern.containsMatchIn(text)) {
                matches++
            }
        }
        
        return matches >= 2 // Need at least 2 patterns to consider it structured
    }
    
    private fun calculateDocumentConfidence(
        textLength: Int,
        hasStructuredContent: Boolean,
        imageAspectRatio: Float,
        textBlocks: Int
    ): Float {
        var confidence = 0f
        
        // Text length factor (more text = more likely to be document)
        confidence += when {
            textLength >= 100 -> 0.3f
            textLength >= 50 -> 0.2f
            textLength >= 20 -> 0.1f
            else -> 0f
        }
        
        // Structured content factor
        if (hasStructuredContent) {
            confidence += 0.3f
        }
        
        // Aspect ratio factor (documents are often rectangular)
        val aspectRatioScore = when {
            imageAspectRatio in 0.7f..1.4f -> 0.1f // Square-ish (could be receipt)
            imageAspectRatio in 0.5f..0.8f -> 0.2f // Portrait (typical document)
            imageAspectRatio in 1.2f..2.0f -> 0.15f // Landscape document
            else -> 0f
        }
        confidence += aspectRatioScore
        
        // Text blocks factor (documents usually have multiple text blocks)
        confidence += when {
            textBlocks >= 5 -> 0.2f
            textBlocks >= 3 -> 0.1f
            textBlocks >= 1 -> 0.05f
            else -> 0f
        }
        
        return confidence.coerceIn(0f, 1f)
    }
    
    fun cleanup() {
        textRecognizer.close()
    }
}
