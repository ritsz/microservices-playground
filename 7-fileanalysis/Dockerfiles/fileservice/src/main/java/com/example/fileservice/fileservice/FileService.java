package com.example.fileservice.fileservice;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
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
import com.google.common.hash.HashFunction;
import com.google.common.io.Files;

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

    public FileInfo create(MultipartFile file) throws NoSuchAlgorithmException, IOException {
        FileEntity entity = getFileEntity(file);
        log.info("Saving entity: {}", entity);
        FileEntity saved = findBySha256(entity.getSha256());
        Long timestamp = System.currentTimeMillis();
        if (saved != null) {
            log.info("Updating using existing record: {}", saved);
            saved.setLastUploadTime(timestamp);
            return convert(fileRepository.save(saved));
        } else {
            log.info("Adding new record: {}", entity);
            ObjectWriteResponse response = minioService.uploadFile(entity.getSavedFileName(), file.getBytes());
            entity.setFirstUploadTime(timestamp);
            entity.setLastUploadTime(timestamp);
            entity.setBucketName(response.bucket());
            entity.setEtag(response.etag());
            entity.setRegion(response.region());
            entity.setVersionId(response.versionId());
            entity.setUploadStatus(FileInfo.UploadStatus.DONE.toString());
            return convert(fileRepository.save(entity));
        }
    }

    public File download(UUID id) {
        FileEntity entity = findById(id);
        return minioService.downloadFile(entity.getOriginalFileName(), entity.getSavedFileName());
    }

    public FileInfo findInfoById(UUID id) {
        if (fileRepository.existsById(id)) {
            return convert(fileRepository.findById(id).get());
        }
        throw new FileServiceException("Not found", HttpStatus.NOT_FOUND);
    }

    private FileEntity findById(UUID id) {
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
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        byte[] hashArray = md.digest(file.getBytes());
        String hash = bytesToHex(hashArray);
        FileEntity entity = new FileEntity();
        entity.setOriginalFileName(file.getOriginalFilename());
        entity.setSavedFileName(UUID.nameUUIDFromBytes(hashArray).toString());
        entity.setSha256(hash);
        entity.setUploadStatus(FileInfo.UploadStatus.INPROGRESS.toString());
        entity.setFileSize(file.getSize());
        return entity;
    }

    private FileInfo convert(FileEntity entity) {
        FileInfo info = new FileInfo();
        info.setId(entity.getId());
        info.setFileName(entity.getOriginalFileName());
        info.setSha256(entity.getSha256());
        info.setUploadStatus(FileInfo.UploadStatus.valueOf(entity.getUploadStatus()));
        info.setFileSize(entity.getFileSize());
        info.setFirstUploadTime(entity.getFirstUploadTime());
        info.setLastUploadTime(entity.getLastUploadTime());
        info.setBucketName(entity.getBucketName());
        info.setEtag(entity.getEtag());
        info.setRegion(entity.getRegion());
        info.setVersionId(entity.getVersionId());
        return info;
    }

    private static final char[] HEX_ARRAY = "0123456789ABCDEF".toCharArray();
    private static String bytesToHex(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = HEX_ARRAY[v >>> 4];
            hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
        }
        return new String(hexChars);
    }
}
