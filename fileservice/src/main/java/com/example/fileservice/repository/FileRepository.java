package com.example.fileservice.repository;

import java.util.UUID;


import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.example.fileservice.model.FileEntity;

@Repository
public interface FileRepository extends JpaRepository<FileEntity, UUID> {
    FileEntity findBySha256(String sha256);
}
