package com.example.fileservice.fileservice;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Optional;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.expression.spel.ast.OpAnd;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.example.fileservice.exception.FileServiceException;
import com.example.fileservice.model.FileEntity;
import com.example.fileservice.model.FileInfo;
import com.example.fileservice.repository.FileRepository;

import io.minio.ObjectWriteResponse;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Service
@AllArgsConstructor
@Slf4j
public class FileService {
    @Autowired
    FileRepository fileRepository;

    @Autowired
    MinioService minioService;

    public FileEntity create(MultipartFile file) throws NoSuchAlgorithmException, IOException {
        FileEntity entity = getFileEntity(file);
        log.info("Saving entity: {}", entity);
        FileEntity saved = findBySha256(entity.getSha256());
        if (saved != null) {
            log.info("Updating using existing record: {}", saved);
            saved.setFileName(entity.getFileName());
            saved.setLastUploadTime(entity.getLastUploadTime());
            return fileRepository.save(saved);
        } else {
            log.info("Adding new record: {}", entity);
//            ObjectWriteResponse response = minioService.uploadFile(file.getOriginalFilename(), file.getBytes());
            Long timestamp = System.currentTimeMillis();
            entity.setFirstUploadTime(timestamp);
            entity.setLastUploadTime(timestamp);
//            entity.setBucketName(response.bucket());
//            entity.setEtag(response.etag());
//            entity.setRegion(response.region());
//            entity.setVersionId(response.versionId());
//            entity.setStatus(FileInfo.UploadStatus.DONE.toString());
            return fileRepository.save(entity);
        }
    }

    public FileEntity findById(UUID id) {
        if (fileRepository.existsById(id)) {
            return fileRepository.findById(id).get();
        }
        throw new FileServiceException("Not found", HttpStatus.NOT_FOUND);
    }

    public FileEntity findBySha256(String sha256) {
        log.info("Checking existing record for SHA: {}", sha256);
        return fileRepository.findBySha256(sha256);
    }

    private FileEntity getFileEntity(MultipartFile file) throws NoSuchAlgorithmException, IOException {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(file.getBytes());
        FileEntity entity = new FileEntity();
        entity.setFileName(file.getOriginalFilename());
        entity.setSha256(hash.toString());
        entity.setUploadStatus(FileInfo.UploadStatus.INPROGRESS.toString());
        entity.setFileSize(file.getSize());
        return entity;
    }
}
