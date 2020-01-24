//
// Created by tom on 1/23/20.
//

#include "gtest/gtest.h"
#include "Trie.h"
#include <vector>

TEST(Trie, simpleadd){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    t.put("a", "yay!");

    std::string out = t.get("a");

    ASSERT_EQ(out, "yay!");
}

TEST(Trie, simpleadd2){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    t.put("a a a a a", "yay!");

    std::string out = t.get("a a a a a");
    ASSERT_EQ(out, "yay!");
    out = t.get("a a a a");
    ASSERT_NE(out, "yay!");
}

TEST(Trie, simpleadd3){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    t.put("a b c a b c", "yay!");

    std::string out = t.get("a b c a b c");

    ASSERT_EQ(out, "yay!");
}

TEST(Trie, miss){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    std::string out = t.get("a a a a a");
    ASSERT_EQ(out, "");
}

TEST(Trie, wathappenwhenoutsidealphabet){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    EXPECT_THROW({
         try{
             std::string out = t.get("d");
         }
         catch( const std::exception& e ) {
             EXPECT_STREQ("d not in alphabet", e.what());
             throw;
         }
    }, std::exception);
}