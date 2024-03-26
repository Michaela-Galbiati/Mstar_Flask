-- Criar o banco de dados
CREATE DATABASE IF NOT EXISTS sistemaro;

-- Usar o banco de dados
USE sistemaro;

-- Criar a tabela Mercadorias
CREATE TABLE IF NOT EXISTS Mercadorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    fabricante VARCHAR(255) NOT NULL,
    numero_registro VARCHAR(255) NOT NULL UNIQUE,
    tipo VARCHAR(255) NOT NULL,
    descricao TEXT NOT NULL,
    quantidade_total_entrada INT DEFAULT 0,
    quantidade_total_saida INT DEFAULT 0,
    disponibilidade INT DEFAULT 0
);

-- Criar a tabela Entrada
CREATE TABLE IF NOT EXISTS Entrada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_mercadoria VARCHAR(255) NOT NULL,
    quantidade INT NOT NULL,
    data_hora DATETIME NOT NULL,
    local VARCHAR(255) NOT NULL,
    FOREIGN KEY (nome_mercadoria) REFERENCES Mercadorias(nome)
);

-- Criar a tabela Saida
CREATE TABLE IF NOT EXISTS Saida (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_mercadoria VARCHAR(255) NOT NULL,
    quantidade INT NOT NULL,
    data_hora DATETIME NOT NULL,
    local VARCHAR(255) NOT NULL,
    FOREIGN KEY (nome_mercadoria) REFERENCES Mercadorias(nome)
);

-- Criar a tabela QuantidadeTotal
CREATE TABLE IF NOT EXISTS QuantidadeTotal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_mercadoria VARCHAR(255) NOT NULL,
    mes_ano VARCHAR(7) NOT NULL,
    quantidade_total_entradas INT DEFAULT 0,
    quantidade_total_saidas INT DEFAULT 0,
    disponibilidade INT DEFAULT 0,
    UNIQUE KEY (nome_mercadoria, mes_ano)
);

-- Criar a tabela Mensal
CREATE TABLE IF NOT EXISTS Mensal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mes_ano VARCHAR(7) NOT NULL,
    quantidade_total_entradas INT DEFAULT 0,
    quantidade_total_saidas INT DEFAULT 0,
    UNIQUE KEY (mes_ano)
);
