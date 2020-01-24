//
// Created by tom on 1/22/20.
//

#include "RERSConnectorV3.h"
#include "subprocess.hpp"

namespace sp = subprocess;

RERSConnectorV3::RERSConnectorV3(std::string &path):
    path(path){

    re_num = std::regex("[0-9]+");
    re_err = std::regex("error_[0-9]+");
    re_invalid = std::regex("Invalid input");
}

std::string RERSConnectorV3::interact(std::string input) {
    //std::cout << input << std::endl;
    //std::cout << path << std::endl;
    // Set up external process

    std::cout << count << std::endl;

    count++;

    auto p = sp::Popen({path}, sp::input{sp::PIPE}, sp::output{sp::PIPE}, sp::error{sp::STDOUT});

    //std::cout << "Set up process" << std::endl;

    // Run external process, send stdin, collect stdout
    std::pair<sp::Buffer, sp::Buffer> comms = p.communicate(input.c_str(), strlen(input.c_str()));

    //std::cout << "Ran process" << std::endl;

    // Convert value from char vector to std::string
    std::string output = std::string(comms.first.buf.begin(), comms.first.buf.end());

    return process_output(output);
}

std::string RERSConnectorV3::interact_fast(std::string input) {

    //std::cout <<"enter interact: \"" << input << "\"" << std::endl;

    int pid = 0;
    int inpipefd[2];
    int outpipefd[2];
    int status;

    pipe(inpipefd);
    pipe(outpipefd);

    pid = fork();

    if (pid == 0)
    {
        // Child
        dup2(outpipefd[0], STDIN_FILENO);
        dup2(inpipefd[1], STDOUT_FILENO);
        dup2(inpipefd[1], STDERR_FILENO);

        //ask kernel to deliver SIGTERM in case the parent dies
        prctl(PR_SET_PDEATHSIG, SIGTERM);

        //replace with given process
        execl(path.c_str(), "rers", (char*) NULL);

        // If we reach this (shouldn't happen):
        perror("Child failed");
        exit(1);
    }
    else if (pid < 0) {
        perror("Failed");
    }
    else {
        //close unused pipe ends
        close(outpipefd[0]);
        close(inpipefd[1]);

        write(outpipefd[1], input.c_str(), strlen(input.c_str()));

        //std::cout << "B waitpid" << std::endl;

        waitpid(pid, &status, 0);

        //std::cout << "A waitpid" << std::endl;

        ssize_t b_read = read(inpipefd[0], rcv_buf, RECVSIZE);
        rcv_buf[b_read] = 0;

        close(outpipefd[1]);
        close(inpipefd[0]);

        //std::cout << "Received answer: "<< std::endl << std::string(rcv_buf) << std::endl;

        std::string output = std::string(rcv_buf);

        return process_output(output);
    }

}

std::string RERSConnectorV3::process_output(std::string &output) {
    std::stringstream ss(output);

    std::vector<std::string> lines;

    // Tokenize
    std::string token;
    std::string prevtoken;
    while (std::getline(ss, token, '\n')) {
        lines.push_back(token);
    }

    std::string result;
    for (int i = 0; i < lines.size(); i++) {
        std::string line = lines[i];

        //std::cout << "Line: " << line << std::endl;

        if (std::regex_match(line, re_invalid)) {
            result = "invalid_input";
        }
        else if (std::regex_search(line, re_num)) {
            result = line;
        }
        else if (std::regex_search(line, re_err)) {
            result = line;
        } else {
            std::cout << "No match" << std::endl;
        }
    }

    return result;

}

