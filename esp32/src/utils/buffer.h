/**
 * ============================================================================
 * buffer.cpp - Circular Buffer Implementation
 * ============================================================================
 */

#include "buffer.h"

CircularBuffer::CircularBuffer(size_t size) {
    bufferSize = size;
    buffer = new uint8_t[size];
    
    head = 0;
    tail = 0;
    full = false;
    
    totalWritten = 0;
    totalRead = 0;
    overflowCount = 0;
    
    mux = portMUX_INITIALIZER_UNLOCKED;
    
    Serial.printf("Circular buffer created: %d bytes\n", size);
}

CircularBuffer::~CircularBuffer() {
    delete[] buffer;
}

bool CircularBuffer::write(uint8_t data) {
    lock();
    
    if (full) {
        overflowCount++;
        unlock();
        return false;
    }
    
    buffer[head] = data;
    head = nextIndex(head);
    
    full = (head == tail);
    
    totalWritten++;
    
    unlock();
    
    return true;
}

size_t CircularBuffer::write(const uint8_t* data, size_t length) {
    if (!data || length == 0) {
        return 0;
    }
    
    lock();
    
    size_t written = 0;
    
    for (size_t i = 0; i < length; i++) {
        if (full) {
            overflowCount++;
            break;
        }
        
        buffer[head] = data[i];
        head = nextIndex(head);
        
        full = (head == tail);
        
        written++;
        totalWritten++;
    }
    
    unlock();
    
    return written;
}

bool CircularBuffer::read(uint8_t* data) {
    if (!data) {
        return false;
    }
    
    lock();
    
    if (isEmpty()) {
        unlock();
        return false;
    }
    
    *data = buffer[tail];
    tail = nextIndex(tail);
    
    full = false;
    
    totalRead++;
    
    unlock();
    
    return true;
}

size_t CircularBuffer::read(uint8_t* data, size_t length) {
    if (!data || length == 0) {
        return 0;
    }
    
    lock();
    
    size_t read_count = 0;
    
    while (read_count < length && !isEmpty()) {
        data[read_count] = buffer[tail];
        tail = nextIndex(tail);
        
        full = false;
        
        read_count++;
        totalRead++;
    }
    
    unlock();
    
    return read_count;
}

bool CircularBuffer::peek(uint8_t* data) {
    if (!data) {
        return false;
    }
    
    lock();
    
    if (isEmpty()) {
        unlock();
        return false;
    }
    
    *data = buffer[tail];
    
    unlock();
    
    return true;
}

size_t CircularBuffer::peek(uint8_t* data, size_t length, size_t offset) {
    if (!data || length == 0) {
        return 0;
    }
    
    lock();
    
    size_t available_data = available();
    
    if (offset >= available_data) {
        unlock();
        return 0;
    }
    
    size_t to_read = min(length, available_data - offset);
    
    size_t index = tail;
    for (size_t i = 0; i < offset; i++) {
        index = nextIndex(index);
    }
    
    for (size_t i = 0; i < to_read; i++) {
        data[i] = buffer[index];
        index = nextIndex(index);
    }
    
    unlock();
    
    return to_read;
}

size_t CircularBuffer::available() {
    lock();
    
    size_t avail;
    
    if (full) {
        avail = bufferSize;
    } else if (head >= tail) {
        avail = head - tail;
    } else {
        avail = bufferSize + head - tail;
    }
    
    unlock();
    
    return avail;
}

size_t CircularBuffer::freeSpace() {
    return bufferSize - available();
}

bool CircularBuffer::isEmpty() {
    lock();
    bool empty = (!full && (head == tail));
    unlock();
    
    return empty;
}

bool CircularBuffer::isFull() {
    lock();
    bool is_full = full;
    unlock();
    
    return is_full;
}

void CircularBuffer::clear() {
    lock();
    
    head = 0;
    tail = 0;
    full = false;
    
    unlock();
}

void CircularBuffer::flush() {
    clear();
}

size_t CircularBuffer::getTotalWritten() {
    lock();
    size_t total = totalWritten;
    unlock();
    
    return total;
}

size_t CircularBuffer::getTotalRead() {
    lock();
    size_t total = totalRead;
    unlock();
    
    return total;
}

size_t CircularBuffer::getOverflowCount() {
    lock();
    size_t count = overflowCount;
    unlock();
    
    return count;
}

size_t CircularBuffer::nextIndex(size_t index) {
    return (index + 1) % bufferSize;
}

void CircularBuffer::lock() {
    portENTER_CRITICAL(&mux);
}

void CircularBuffer::unlock() {
    portEXIT_CRITICAL(&mux);
}
