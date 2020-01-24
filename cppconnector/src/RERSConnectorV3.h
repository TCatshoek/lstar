//
// Created by tom on 1/22/20.
//

#ifndef CONNECTOR_RERSCONNECTORV3_H
#define CONNECTOR_RERSCONNECTORV3_H

#define RECVSIZE 1024 * 1024

#include <regex>
#include <string>

#include <unistd.h>
#include <sys/wait.h>
#include <sys/prctl.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

class RERSConnectorV3 {
private:
    std::string path;
    std::regex re_num;
    std::regex re_err;
    std::regex re_invalid;

    // 1MB Receive buffer
    char rcv_buf[RECVSIZE];

    int count = 0;

public:
    RERSConnectorV3(std::string &path);

    std::string process_output(std::string &output);

    std::string interact(std::string input);
    std::string interact_fast(std::string input);
};


#endif //CONNECTOR_RERSCONNECTORV3_H
