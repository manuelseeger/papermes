package com.papermes.documentscanner.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.Date

@Entity(tableName = "documents")
data class DocumentEntity(
    @PrimaryKey val id: String,
    val filePath: String,
    val fileName: String,
    val mimeType: String,
    val size: Long,
    val dateAdded: Date,
    val dateModified: Date,
    val width: Int,
    val height: Int,
    val isProcessed: Boolean = false,
    val isDocument: Boolean = false,
    val isSent: Boolean = false,
    val confidence: Float = 0f,
    val retryCount: Int = 0,
    val lastRetryDate: Date? = null,
    val errorMessage: String? = null
)
