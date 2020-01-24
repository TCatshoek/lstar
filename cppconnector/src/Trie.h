//
// Created by tom on 1/23/20.
//

#ifndef CONNECTOR_TRIE_H
#define CONNECTOR_TRIE_H

#include <string>
#include <vector>
#include <memory>
#include <sstream>

class TrieNode {
public:
    TrieNode(size_t n_children):
        children(std::vector<std::unique_ptr<TrieNode>>(n_children)){}

    std::vector<std::unique_ptr<TrieNode>> children;
    std::string value;
};

class Trie {
public:
    Trie(std::vector<std::string> alphabet, char separator);

    void put(const std::string &key, const std::string &value);

    std::string get(const std::string &key);

private:
    int getAlphabetIdx(std::string a);

    std::vector<std::string> alphabet;
    size_t alphabetsize;

    char separator;

    std::unique_ptr<TrieNode> root;
};


#endif //CONNECTOR_TRIE_H
