package com.example.fileservice.controller;

import static com.example.fileservice.UriPaths.DOMAIN_ROOT;

import java.io.IOException;
import java.security.NoSuchAlgorithmException;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.fileservice.fileservice.FileService;
import com.example.fileservice.fileservice.MinioService;
import com.example.fileservice.model.FileEntity;
import com.example.fileservice.model.FileInfo;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RestController
@RequestMapping(DOMAIN_ROOT)
@Validated
@AllArgsConstructor
@Slf4j
public class FileController {

    @Autowired
    FileService fileService;

    @Autowired
    MinioService minioService;

    @PostMapping
    public FileEntity uploadFile(@RequestParam("file") MultipartFile multipartFile)
        throws IOException, NoSuchAlgorithmException {
        minioService.uploadFile(multipartFile.getOriginalFilename(), multipartFile.getBytes());
        return fileService.create(multipartFile);
    }
}
