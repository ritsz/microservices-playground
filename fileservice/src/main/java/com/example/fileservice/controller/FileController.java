package com.example.fileservice.controller;

import static com.example.fileservice.UriPaths.DOMAIN_ROOT;

import javax.annotation.Resource;
import java.io.IOException;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.fileservice.fileservice.FileService;
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

    @PostMapping
    public FileInfo uploadFile(@RequestParam("file") MultipartFile multipartFile)
        throws IOException, NoSuchAlgorithmException {
        return fileService.create(multipartFile);
    }

    @GetMapping("/{id}")
    public FileInfo getFileById(@PathVariable("id") UUID id) {
        return fileService.findById(id);
    }
//
//    @PostMapping("{id}/download")
//    public ResponseEntity<Resource> downloadFile(@PathVariable("id") UUID id) {
//        return ResponseEntity.ok();
//    }
}
