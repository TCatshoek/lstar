//
// Created by tom on 1/23/20.
//

#include "gtest/gtest.h"
#include "RERSConnectorV3.h"
#include <vector>
#include <stdlib.h>
#include <time.h>
#include <chrono>

using namespace std::chrono;

TEST(Trie, time){
    std::vector<std::string> alphabet = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"};

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

    RERSConnectorV3 r("/home/tom/projects/lstar/rers/TrainingSeqReachRers2019/Problem11/Problem11");


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

