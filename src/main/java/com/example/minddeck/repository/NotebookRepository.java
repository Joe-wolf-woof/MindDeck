package com.example.minddeck.repository;
import org.springframework.data.jpa.repository.JpaRepository;

import com.example.minddeck.model.Notebook;
public interface NotebookRepository extends JpaRepository<Notebook, Long> {}