package com.papermes.documentscanner.repository

import com.papermes.documentscanner.data.DocumentDao
import com.papermes.documentscanner.data.DocumentEntity
import kotlinx.coroutines.flow.Flow
import java.util.Date

class DocumentRepository(private val documentDao: DocumentDao) {
    
    fun getUnprocessedDocuments(): Flow<List<DocumentEntity>> {
        return documentDao.getUnprocessedDocuments()
    }
    
    fun getUnsyncedDocuments(): Flow<List<DocumentEntity>> {
        return documentDao.getUnsyncedDocuments()
    }
    
    suspend fun getDocumentById(id: String): DocumentEntity? {
        return documentDao.getDocumentById(id)
    }
    
    fun getAllDocuments(): Flow<List<DocumentEntity>> {
        return documentDao.getAllDocuments()
    }
    
    suspend fun insertDocument(document: DocumentEntity) {
        documentDao.insertDocument(document)
    }
    
    suspend fun insertDocuments(documents: List<DocumentEntity>) {
        documentDao.insertDocuments(documents)
    }
    
    suspend fun updateDocument(document: DocumentEntity) {
        documentDao.updateDocument(document)
    }
    
    suspend fun updateDocumentProcessingResult(id: String, isDocument: Boolean, confidence: Float) {
        documentDao.updateDocumentProcessingResult(id, isDocument, confidence)
    }
    
    suspend fun markDocumentAsSent(id: String) {
        documentDao.markDocumentAsSent(id)
    }
    
    suspend fun updateDocumentRetry(id: String, retryCount: Int, lastRetryDate: Date, errorMessage: String?) {
        documentDao.updateDocumentRetry(id, retryCount, lastRetryDate, errorMessage)
    }
    
    suspend fun deleteOldDocuments(cutoffDate: Date) {
        documentDao.deleteOldDocuments(cutoffDate)
    }
    
    suspend fun getDocumentCount(): Int {
        return documentDao.getDocumentCount()
    }
}
