#!/bin/bash

read -d '' yaml <<__EOT__
username: jdoe
name: John Doe
email: john.doe@foo.bar
ssh_key: ssh-dss AAAAB3NzaC1kc3MAAACBAKWqxsX8UwfzKH+oZITNDgb6G3oKhEgiYUxBPS6uaBzwRiRAZFKNV9qaszKISBfQj2g94D85tckch+VRGZ0d/xyScKOhWS7RZqc0gkWQsyNrW9lS760h6H2aQoMai5v3LozIjBTI09M62cJhYMkvKAI9meug+Lk+o9FNf4aYLL9dAAAAFQD9KmYisfyIZ2riEZt+/Zurnsjl8QAAAIEAn1MAw9ZkE4CEq8Gl6kaALIfy7UQEru/LgoRrstzq1Y3LRwW0v6XBWcXkgwm/CEalet/8TrI9DM1Yv2rNfv74la/MhX1OMCYWJgHfxhkAzR1R09SNNdtxy1QenjiHt10+ghyZp9I+M+G7FZ++tYdw6VTqS3W09D2Efa/wxSLcOYAAAACAYjMECizhzw59+Tu7Sr1P6zsbZ3+qT7tNOOZQlwzD71WBrrZYagQOThyMrej8qc2Z64mtWFQ/QNviVNJKF/OlMMcvdhIc0Q8H4x3xYMXIZKRRPb/SDpTzGVQRzck/D11NMXpq4qu4ruF8q1evzOzMGoSAmC0By1v0js0kkk6kXEe= jdoe@foobar
__EOT__

curl -v -X POST -H 'Content-type: application/yaml' -d "${yaml}" http://127.0.0.1:5000/users