package com.papermes.documentscanner.utils

import android.content.ContentResolver
import android.content.ContentUris
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.MediaStore
import android.util.Log
import com.papermes.documentscanner.data.DocumentEntity
import java.util.Date

class MediaScanner(private val context: Context) {
    
    companion object {
        private const val TAG = "MediaScanner"
    }
    
    fun scanForNewImages(lastScanTime: Long): List<DocumentEntity> {
        val images = mutableListOf<DocumentEntity>()
        
        val projection = arrayOf(
            MediaStore.Images.Media._ID,
            MediaStore.Images.Media.DISPLAY_NAME,
            MediaStore.Images.Media.DATA,
            MediaStore.Images.Media.SIZE,
            MediaStore.Images.Media.MIME_TYPE,
            MediaStore.Images.Media.DATE_ADDED,
            MediaStore.Images.Media.DATE_MODIFIED,
            MediaStore.Images.Media.WIDTH,
            MediaStore.Images.Media.HEIGHT
        )
        
        val selection = "${MediaStore.Images.Media.DATE_ADDED} > ?"
        val selectionArgs = arrayOf((lastScanTime / 1000).toString()) // MediaStore uses seconds
        val sortOrder = "${MediaStore.Images.Media.DATE_ADDED} DESC"
        
        try {
            val cursor: Cursor? = context.contentResolver.query(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                projection,
                selection,
                selectionArgs,
                sortOrder
            )
            
            cursor?.use {
                val idColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media._ID)
                val nameColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DISPLAY_NAME)
                val dataColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATA)
                val sizeColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.SIZE)
                val mimeTypeColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.MIME_TYPE)
                val dateAddedColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATE_ADDED)
                val dateModifiedColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATE_MODIFIED)
                val widthColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.WIDTH)
                val heightColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.HEIGHT)
                
                while (it.moveToNext()) {
                    val id = it.getLong(idColumn)
                    val name = it.getString(nameColumn)
                    val data = it.getString(dataColumn)
                    val size = it.getLong(sizeColumn)
                    val mimeType = it.getString(mimeTypeColumn)
                    val dateAdded = it.getLong(dateAddedColumn) * 1000 // Convert to milliseconds
                    val dateModified = it.getLong(dateModifiedColumn) * 1000
                    val width = it.getInt(widthColumn)
                    val height = it.getInt(heightColumn)
                    
                    // Skip if this is not a supported image type
                    if (!isSupportedImageType(mimeType)) {
                        continue
                    }
                    
                    val document = DocumentEntity(
                        id = id.toString(),
                        filePath = data,
                        fileName = name,
                        mimeType = mimeType,
                        size = size,
                        dateAdded = Date(dateAdded),
                        dateModified = Date(dateModified),
                        width = width,
                        height = height
                    )
                    
                    images.add(document)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error scanning for new images", e)
        }
        
        Log.i(TAG, "Found ${images.size} new images since $lastScanTime")
        return images
    }
    
    private fun isSupportedImageType(mimeType: String): Boolean {
        return mimeType.startsWith("image/") && 
               (mimeType.contains("jpeg") || 
                mimeType.contains("jpg") || 
                mimeType.contains("png") || 
                mimeType.contains("webp"))
    }
    
    fun getImageUri(imageId: String): Uri {
        return ContentUris.withAppendedId(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            imageId.toLong()
        )
    }
}
