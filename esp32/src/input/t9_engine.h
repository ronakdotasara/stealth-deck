/**
 * ============================================================================
 * t9_engine.h - T9 Text Entry Engine
 * ============================================================================
 * Version: 1.0.0
 * Date: 2025-11-24
 * Author: Stealth Deck Project
 * License: MIT
 * 
 * ============================================================================
 * DESCRIPTION:
 * T9 predictive text entry system for keypad input.
 * Converts numeric key sequences to text using dictionary lookup.
 * 
 * Features:
 * - Predictive text from numeric input
 * - Word suggestions
 * - Multiple word matches
 * - Punctuation handling
 * - Space and special characters
 * 
 * ============================================================================
 */

#ifndef T9_ENGINE_H
#define T9_ENGINE_H

#include <Arduino.h>

#define MAX_WORD_LENGTH 32
#define MAX_SUGGESTIONS 5
#define DICTIONARY_SIZE 1000

enum T9Mode {
    T9_MODE_PREDICTIVE,
    T9_MODE_MULTI_TAP,
    T9_MODE_NUMERIC
};

struct T9Suggestion {
    char word[MAX_WORD_LENGTH];
    uint16_t frequency;
};

class T9Engine {
public:
    T9Engine();
    
    void begin();
    void setMode(T9Mode mode);
    T9Mode getMode();
    
    void handleKey(uint8_t key);
    void handleBackspace();
    void handleSpace();
    void handleNextSuggestion();
    void clear();
    
    const char* getCurrentWord();
    const char* getCurrentInput();
    
    T9Suggestion* getSuggestions(uint8_t& count);
    uint8_t getSuggestionCount();
    void selectSuggestion(uint8_t index);
    
    bool addToUserDictionary(const char* word);
    void clearUserDictionary();
    
private:
    T9Mode currentMode;
    
    char inputSequence[MAX_WORD_LENGTH];
    uint8_t inputLength;
    
    char currentWord[MAX_WORD_LENGTH];
    
    T9Suggestion suggestions[MAX_SUGGESTIONS];
    uint8_t suggestionCount;
    uint8_t selectedSuggestion;
    
    unsigned long lastKeyTime;
    uint8_t lastKey;
    uint8_t tapCount;
    
    const char* keyMap[10];
    
    void updateSuggestions();
    void findMatches(const char* sequence);
    bool matchesSequence(const char* word, const char* sequence);
    
    void multiTapInput(uint8_t key);
    char getMultiTapChar(uint8_t key, uint8_t tapCount);
    
    void loadDictionary();
    bool isInDictionary(const char* word);
};

#endif
