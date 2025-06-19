package com.papermes.documentscanner.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface DocumentDao {
    
    @Query("SELECT * FROM documents WHERE isProcessed = 0 ORDER BY dateAdded DESC")
    fun getUnprocessedDocuments(): Flow<List<DocumentEntity>>
    
    @Query("SELECT * FROM documents WHERE isDocument = 1 AND isSent = 0 ORDER BY dateAdded DESC")
    fun getUnsyncedDocuments(): Flow<List<DocumentEntity>>
    
    @Query("SELECT * FROM documents WHERE id = :id")
    suspend fun getDocumentById(id: String): DocumentEntity?
    
    @Query("SELECT * FROM documents ORDER BY dateAdded DESC")
    fun getAllDocuments(): Flow<List<DocumentEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocument(document: DocumentEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocuments(documents: List<DocumentEntity>)
    
    @Update
    suspend fun updateDocument(document: DocumentEntity)
    
    @Query("UPDATE documents SET isProcessed = 1, isDocument = :isDocument, confidence = :confidence WHERE id = :id")
    suspend fun updateDocumentProcessingResult(id: String, isDocument: Boolean, confidence: Float)
    
    @Query("UPDATE documents SET isSent = 1 WHERE id = :id")
    suspend fun markDocumentAsSent(id: String)
    
    @Query("UPDATE documents SET retryCount = :retryCount, lastRetryDate = :lastRetryDate, errorMessage = :errorMessage WHERE id = :id")
    suspend fun updateDocumentRetry(id: String, retryCount: Int, lastRetryDate: java.util.Date, errorMessage: String?)
    
    @Query("DELETE FROM documents WHERE dateAdded < :cutoffDate")
    suspend fun deleteOldDocuments(cutoffDate: java.util.Date)
    
    @Query("SELECT COUNT(*) FROM documents WHERE isDocument = 1")
    suspend fun getDocumentCount(): Int
}
