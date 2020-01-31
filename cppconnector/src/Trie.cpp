//
// Created by tom on 1/23/20.
//


#include "Trie.h"

Trie::Trie(std::vector<std::string> alphabet, char separator):
    alphabet(alphabet),
    alphabetsize(alphabet.size()),
    separator(std::string(&separator)){

    root = std::make_unique<TrieNode>(alphabetsize);
}

Trie::Trie(std::vector<std::string> alphabet, std::string separator):
    alphabet(alphabet),
    alphabetsize(alphabet.size()),
    separator(std::move(separator)){

    root = std::make_unique<TrieNode>(alphabetsize);
}

void Trie::tokenize(char* string) {
    char* pch;
    pch = strtok(string, separator.c_str());

    uint bufidx = 0;
    while (pch != NULL) {
        tokbuf[bufidx] = pch;
        pch = strtok(NULL, separator.c_str());
        bufidx++;
    }
    n_toks = bufidx;
}


void Trie::put(const std::string &key, const std::string &value) {
    // Tokenize key
    tokenize(&key[0]);

    // Start at root node
    TrieNode* cur_node = root.get();

    for (uint i = 0; i < n_toks; i++) {
        std::string_view token(tokbuf[i]);

        // Look up the alphabet index of this token and grab the pointer to the next node
        int aidx = getAlphabetIdx(token);
        TrieNode* next_node = cur_node->children[aidx];

        // If node does not exits yet, create it
        if (!next_node) {
            next_node = new TrieNode(alphabetsize);
        }

        // If we reached the end of the tokens, store the value
        if (i == n_toks - 1) {
            next_node->value = value;
            return;
        }
        // Else, continue traversing the tree
        else {
            cur_node = next_node;
        }
    }
}

int Trie::getAlphabetIdx(const std::string_view &a) {
    for (uint i = 0; i < alphabetsize; i++) {
        if (a == alphabet[i]) {
            return i;
        }
    }
    throw std::runtime_error(std::string(a) + " not in alphabet");
}

std::string Trie::get(const std::string &key) {
    // Tokenize key
    std::vector<std::string> tokens;
    std::stringstream s(key);

    std::string token;

    while (std::getline(s, token, separator[0])) {
        tokens.push_back(token);
    }

    // Start at root node
    TrieNode* cur_node = root.get();

    for (uint i = 0; i < tokens.size(); i++) {
        token = tokens[i];

        // Look up the alphabet index of this token and grab the pointer to the next node
        int aidx = getAlphabetIdx(std::string_view(token));
        TrieNode* next_node = cur_node->children[aidx];

        // If node does not exist, return empty string
        if (!next_node) {
            return "";
        }
        // If reached end of key, return the value
        if (i == tokens.size() - 1) {
            return next_node->value;
        }
        // Else, continue traversing the tree
        else {
            cur_node = next_node;
        }
    }
}




