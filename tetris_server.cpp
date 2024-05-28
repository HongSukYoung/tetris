#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>

#define PORT 4407
#define MAX_CLIENTS 5
#define MAX_DATA_SIZE 1024

struct Client {
    int socket;
    struct sockaddr_in address;
};

struct Client clients[MAX_CLIENTS];
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

void *handle_client(void *arg) {
    struct Client *client = (struct Client *)arg;
    char data[MAX_DATA_SIZE];

    while (1) {
        ssize_t bytes_received = recv(client->socket, data, sizeof(data), 0);
        if (bytes_received <= 0) {
            break;
        }

        pthread_mutex_lock(&mutex);

        for (int i = 0; i < MAX_CLIENTS; ++i) {
            if (clients[i].socket != -1 && clients[i].socket != client->socket) {
                send(clients[i].socket, data, bytes_received, 0);
            }
        }

        pthread_mutex_unlock(&mutex);
    }

    close(client->socket);

    pthread_mutex_lock(&mutex);
    for (int i = 0; i < MAX_CLIENTS; ++i) {
        if (&clients[i] == client) {
            clients[i].socket = -1;
            break;
        }
    }
    pthread_mutex_unlock(&mutex);

    free(client);
    return NULL;
}

int main() {
    int server_socket, client_socket;
    struct sockaddr_in server_address, client_address;
    socklen_t client_address_len = sizeof(client_address);
    pthread_t thread_id;

    // Initialize clients array
    for (int i = 0; i < MAX_CLIENTS; ++i) {
        clients[i].socket = -1;
    }

    // Create socket
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    // Set up server address
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = INADDR_ANY;
    server_address.sin_port = htons(PORT);

    // Bind the socket
    if (bind(server_socket, (struct sockaddr *)&server_address, sizeof(server_address)) == -1) {
        perror("Binding failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    // Listen for connections
    if (listen(server_socket, MAX_CLIENTS) == -1) {
        perror("Listening failed");
        close(server_socket);
        exit(EXIT_FAILURE);
    }

    printf("서버온티비\n");

    while (1) {
        // Accept a connection
        client_socket = accept(server_socket, (struct sockaddr *)&client_address, &client_address_len);
        if (client_socket == -1) {
            perror("Acceptance failed");
            continue;
        }

        // Find an available slot in the clients array
        pthread_mutex_lock(&mutex);
        int i;
        for (i = 0; i < MAX_CLIENTS; ++i) {
            if (clients[i].socket == -1) {
                clients[i].socket = client_socket;
                clients[i].address = client_address;
                break;
            }
        }
        pthread_mutex_unlock(&mutex);

        if (i == MAX_CLIENTS) {
            fprintf(stderr, "Too many clients. Connection rejected.\n");
            close(client_socket);
            continue;
        }

        // Create a thread to handle the client
        struct Client *client_info = malloc(sizeof(struct Client));
        *client_info = clients[i];
        if (pthread_create(&thread_id, NULL, handle_client, client_info) != 0) {
            perror("Thread creation failed");
            close(client_socket);
            continue;
        }

        pthread_detach(thread_id);
    }

    close(server_socket);
    return 0;
}
