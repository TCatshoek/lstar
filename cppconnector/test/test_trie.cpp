//
// Created by tom on 1/23/20.
//

#include "gtest/gtest.h"
#include "Trie.h"
#include <vector>
#include <stdlib.h>
#include <time.h>
#include <chrono>

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
         catch( const std::runtime_error& e ) {
             EXPECT_STREQ("d not in alphabet", e.what());
             throw;
         }
    }, std::exception);
}


using namespace std::chrono;

TEST(Trie, time){
    std::vector<std::string> alphabet = {"a", "b", "c"};
    Trie t = Trie(alphabet, ' ');

    srand(time(NULL));

    std::vector<std::string> keys;
    for (uint i = 0; i < 100000; i++) {
        std::string tmp = "";

        for (uint j = 0 ; j < 200; j++) {
            tmp += alphabet[rand() % alphabet.size()];
            if(j < 199) {
                tmp += " ";
            }
        }

        keys.push_back(tmp);
    }

    std::string a = "a";
    for (std::string key : keys) {
        t.put(key, a);
    }


    milliseconds start = duration_cast< milliseconds >(
            system_clock::now().time_since_epoch()
    );

    a = "a";
    for (std::string key : keys) {
        t.put(key, a);
    }

    milliseconds end = duration_cast< milliseconds >(
            system_clock::now().time_since_epoch()
    );

    milliseconds total = end - start;
    std::cout << std::endl << "adding took " << total.count() << "ms" << std::endl;



    start = duration_cast< milliseconds >(
            system_clock::now().time_since_epoch()
    );

    for (std::string key : keys) {
        std::string o = t.get(key);
    }

    end = duration_cast< milliseconds >(
            system_clock::now().time_since_epoch()
    );

    total = end - start;
    std::cout << "getting took " << total.count() << "ms" << std::endl;

    ASSERT_TRUE(true);
}

