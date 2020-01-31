//
// Created by tom on 1/23/20.
//

#ifndef CONNECTOR_TRIE_H
#define CONNECTOR_TRIE_H

#include <string>
#include <vector>
#include <memory>
#include <sstream>

#include <stdio.h>
#include <string.h>

class TrieNode {
public:
    TrieNode(size_t n_children):
        children(std::vector<TrieNode*>(n_children)){}

    std::vector<TrieNode*> children;
    std::string value;
};

class Trie {
public:
    Trie(std::vector<std::string> alphabet, std::string separator);
    Trie(std::vector<std::string> alphabet, char separator);

    void put(const std::string &key, const std::string &value);

    std::string get(const std::string &key);

private:
    int getAlphabetIdx(const std::string_view &a);

    void tokenize(char* string);
    std::vector<char*> tokbuf = std::vector<char*>(1024);
    uint n_toks = 0;

    std::vector<std::string> alphabet;
    size_t alphabetsize;

    std::string separator;

    std::unique_ptr<TrieNode> root;
};


#endif //CONNECTOR_TRIE_H
