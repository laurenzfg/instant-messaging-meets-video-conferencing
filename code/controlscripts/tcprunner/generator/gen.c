// gen sends a TCP stream with the maximal possible bandwidth from a client and
// a server running gen.
// The congestion control algorithm can be chosen on the client side from within
// the selection that the host Linux Kernel offers AND have a number defined in this C program.
// Currently: reno, bbr and cubic
//
// Usage: %s     [-s](be a) server [-h]ost [-p]ort [-t]imeout(seconds) [-c]ongControlAlgo
//               [-r]eceive (client only; means receive stream from server. default: send to server)
//
// (c) 2021 Laurenz Grote, (c) 2020 Constantin Sander

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h> 
#include <sys/socket.h> 
#include <sys/types.h>
#include <sys/wait.h>
#include <strings.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <limits.h>
#include <pthread.h>

#include <errno.h>
#include <math.h>

#define BLKSIZE (1024 * 1024)

const char* helpstring = "Usage: %s     [-s](be a) server [-h]ost [-p]ort [-t]imeout(seconds) [-c]ongControlAlgo\n[-r]eceive (client only; means receive stream from server. default: send to server)\n";

char buf[BLKSIZE];

#define NOCONG 4
char* congs[NOCONG] = {"bbr", "cubic", "reno", "bbr2"};

#define MAXNOCHILDREN 10
size_t childPIDs_i = 0;
int childPIDs[10];

int sockfd;

char* cong_from_nr(uint8_t no, uint8_t* len) {
    if(no >= NOCONG) {
        return 0;
    }
    *len = strlen(congs[no]);
    return congs[no];
}

uint8_t cong_to_nr(char* cong) {
    if(strcmp(cong, "bbr")   == 0) return 0;
    if(strcmp(cong, "cubic") == 0) return 1;
    if(strcmp(cong, "reno")  == 0) return 2;
    if(strcmp(cong, "bbr2")  == 0) return 3;
    return 3;
}

void server_session() { // this has to be called in a child process where sockfd is set to the new socket given by accept()
    char tmpbuf;
    if(recv(sockfd, &tmpbuf, 1, 0) != 1) {
        return;
    }
    bool sending = tmpbuf & 0x01;
    uint8_t congno = tmpbuf >> 1;
    uint8_t conglen;
    char* cong = cong_from_nr(congno, &conglen);
    if(cong == 0) {
        close(sockfd);
        return;
    }
    fprintf(stderr, "use cong %s\n", cong);
    if (setsockopt(sockfd, IPPROTO_TCP, TCP_CONGESTION, cong, conglen) < 0) {
        perror("setsockopt cong failed");
        close(sockfd);
        return;
    }
    if(sending) {
        for(;;) {
            if (send(sockfd, buf, BLKSIZE, 0) <= 0){
                return;
            }
        }
    }
    else {
        for(;;) {
            if(recv(sockfd, buf, BLKSIZE, 0) <= 0) {
                return;
            }
        }
    }
}

void server_accept() {
    for(;;) {
        int s = accept(sockfd, NULL, NULL);
        if(s < 0) {
            perror("accept failed");
            exit(1);
        }
        pid_t childPID = fork();
        if (childPID == -1) {
            perror("fork failed");
        } else if (childPID==0) {
            // we operate on the new socket
            sockfd = s;
            // we do not have any children
            childPIDs_i = 0;

            server_session();
        }
        // main process just holds ready to accept a new connection
        // but track the child
        childPIDs[childPIDs_i++] = childPID;
        // we do not intend to use the socket (other process will)
        close(s);
    }
}

void client_recv() {
    for(;;) {
        if (recv(sockfd, buf, BLKSIZE, 0) <= 0){
            perror("recv failed");
            exit (1);
        }
    }
}

void client_send() {
    for(;;) {
        if (send(sockfd, buf, BLKSIZE, 0) <= 0){
            perror("send failed");
            exit (1);
        }
    }
}

/* Close Socket on SIGTERM */
void sigtermHandler(int sig_num)
{
    // Kill all children
    for (size_t i = 0; i < childPIDs_i; i++)
    {
        int pid = childPIDs[i];
        fprintf(stderr, "Send kill signal to %d\n", pid);
        kill(pid, SIGTERM);
        waitpid(pid, 0, 0);
        fprintf(stderr, "Resumed from waiting for %d\n", pid);
    }
    
    close(sockfd);
    fprintf(stderr, "Process %d orderly finished \n", getpid());
    fflush(stdout);
    fflush(stderr);
    exit(0);
}

int main(int argc, char *argv[])
{
    signal(SIGINT, sigtermHandler);
    signal(SIGTERM, sigtermHandler);

    char *cong  = "cubic";
    int port    = 5001;
    bool server = false;
    int opt;
    char *host  = "localhost";
    bool receive = false;

    if (argc == 1) {
        fprintf(stderr, helpstring, argv[0]);
        exit(EXIT_FAILURE);
    }

    while ((opt = getopt(argc, argv, "h:sp:c:r")) != -1) {
        switch (opt) {
        case 'h': host    = optarg; break;
        case 'p': port    = (int) strtol(optarg, (char **)NULL, 10); break;
        case 's': server  = true; break;
        case 'c': cong    = optarg; break;
        case 'r': receive = true; break;
        default:
            fprintf(stderr, helpstring, argv[0]);
            exit(EXIT_FAILURE);
        }
    }

    for(int i = 0; i < BLKSIZE; i++) {
        buf[i] = '0' + (i % 10);
    }

    if(server) {
        struct sockaddr_in servaddr;
        bzero(&servaddr, sizeof(servaddr)); 
        // assign IP, PORT 
        servaddr.sin_family = AF_INET; 
        servaddr.sin_addr.s_addr = htonl(INADDR_ANY); 
        servaddr.sin_port = htons(port);
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if(sockfd < 0) {
            perror("socket creation failed");
            exit(1);
        }
        int reuse_addr = 1;
        if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &reuse_addr, sizeof(reuse_addr)) < 0) {
            perror("setsockopt reuseaddr failed"); 
            close(sockfd);
            exit(1); 
        }
        if (bind(sockfd, (struct sockaddr*) &servaddr, sizeof(servaddr))) { 
            perror("bind failed"); 
            close(sockfd);
            exit(1); 
        }
        if(listen(sockfd, INT_MAX)) {
            perror("listen failed");
            close(sockfd);
            exit(1);
        }
        server_accept();
    }
    else {
        struct sockaddr_in servaddr;
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if(sockfd < 0) {
            perror("socket creation failed");
            exit(1);
        }
        struct hostent *he;
        if ((he=gethostbyname(host)) == NULL) {
            perror("gethostbyname failed");
            close(sockfd);
            exit(1);
        }
        bzero(&servaddr, sizeof(servaddr)); 
        servaddr.sin_family = AF_INET;
        servaddr.sin_port = htons(port);
        servaddr.sin_addr = *((struct in_addr *)he->h_addr);
        fprintf(stderr, "set congestion control: %s\n",cong);
        if (setsockopt(sockfd, IPPROTO_TCP, TCP_CONGESTION, cong, strlen(cong)) < 0) {
            perror("setsockopt cong failed");
            close(sockfd);
            exit(1);
        }
        if (connect(sockfd, (struct sockaddr *)&servaddr, sizeof(struct sockaddr)) == -1) {
            perror("connect failed");
            close(sockfd);
            exit(1);
        }
        uint8_t tmpbuf = (receive & 0x01) | (cong_to_nr(cong) << 1);
        if(send(sockfd, &tmpbuf, 1, 0) != 1) {
            perror("send error");
            exit(1);
        }
        pthread_t thread;
        if(receive) {
            client_recv();
        }
        else {
            client_send();
        }
    }
}
