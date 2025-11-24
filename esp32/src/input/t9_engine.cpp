/**
 * ============================================================================
 * t9_engine.cpp - T9 Text Entry Implementation
 * ============================================================================
 */

#include "t9_engine.h"

// Common English words for basic T9 dictionary
const char* commonWords[] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "hello", "yes", "no", "ok", "thanks", "please", "sorry", "help", "call", "text"
};

const int dictionarySize = sizeof(commonWords) / sizeof(commonWords[0]);

T9Engine::T9Engine() {
    currentMode = T9_MODE_PREDICTIVE;
    inputLength = 0;
    suggestionCount = 0;
    selectedSuggestion = 0;
    lastKeyTime = 0;
    lastKey = 0;
    tapCount = 0;
    
    keyMap[0] = " 0";
    keyMap[1] = ".,!?1";
    keyMap[2] = "abc2";
    keyMap[3] = "def3";
    keyMap[4] = "ghi4";
    keyMap[5] = "jkl5";
    keyMap[6] = "mno6";
    keyMap[7] = "pqrs7";
    keyMap[8] = "tuv8";
    keyMap[9] = "wxyz9";
    
    memset(inputSequence, 0, sizeof(inputSequence));
    memset(currentWord, 0, sizeof(currentWord));
}

void T9Engine::begin() {
    loadDictionary();
}

void T9Engine::setMode(T9Mode mode) {
    currentMode = mode;
    clear();
}

T9Mode T9Engine::getMode() {
    return currentMode;
}

void T9Engine::handleKey(uint8_t key) {
    if (key < '0' || key > '9') {
        return;
    }
    
    if (currentMode == T9_MODE_PREDICTIVE) {
        if (inputLength < MAX_WORD_LENGTH - 1) {
            inputSequence[inputLength++] = key;
            inputSequence[inputLength] = '\0';
            
            updateSuggestions();
            
            if (suggestionCount > 0) {
                strcpy(currentWord, suggestions[0].word);
            }
        }
    } else if (currentMode == T9_MODE_MULTI_TAP) {
        multiTapInput(key);
    } else {
        if (inputLength < MAX_WORD_LENGTH - 1) {
            inputSequence[inputLength++] = key;
            inputSequence[inputLength] = '\0';
            strcpy(currentWord, inputSequence);
        }
    }
}

void T9Engine::handleBackspace() {
    if (inputLength > 0) {
        inputLength--;
        inputSequence[inputLength] = '\0';
        
        if (currentMode == T9_MODE_PREDICTIVE) {
            updateSuggestions();
            if (suggestionCount > 0) {
                strcpy(currentWord, suggestions[0].word);
            } else {
                currentWord[0] = '\0';
            }
        } else {
            strcpy(currentWord, inputSequence);
        }
    }
}

void T9Engine::handleSpace() {
    clear();
}

void T9Engine::handleNextSuggestion() {
    if (suggestionCount > 0) {
        selectedSuggestion = (selectedSuggestion + 1) % suggestionCount;
        strcpy(currentWord, suggestions[selectedSuggestion].word);
    }
}

void T9Engine::clear() {
    inputLength = 0;
    suggestionCount = 0;
    selectedSuggestion = 0;
    
    memset(inputSequence, 0, sizeof(inputSequence));
    memset(currentWord, 0, sizeof(currentWord));
}

const char* T9Engine::getCurrentWord() {
    return currentWord;
}

const char* T9Engine::getCurrentInput() {
    return inputSequence;
}

T9Suggestion* T9Engine::getSuggestions(uint8_t& count) {
    count = suggestionCount;
    return suggestions;
}

uint8_t T9Engine::getSuggestionCount() {
    return suggestionCount;
}

void T9Engine::selectSuggestion(uint8_t index) {
    if (index < suggestionCount) {
        selectedSuggestion = index;
        strcpy(currentWord, suggestions[index].word);
    }
}

void T9Engine::updateSuggestions() {
    suggestionCount = 0;
    
    findMatches(inputSequence);
    
    selectedSuggestion = 0;
}

void T9Engine::findMatches(const char* sequence) {
    for (int i = 0; i < dictionarySize && suggestionCount < MAX_SUGGESTIONS; i++) {
        if (matchesSequence(commonWords[i], sequence)) {
            strcpy(suggestions[suggestionCount].word, commonWords[i]);
            suggestions[suggestionCount].frequency = 100 - i;
            suggestionCount++;
        }
    }
}

bool T9Engine::matchesSequence(const char* word, const char* sequence) {
    int seqLen = strlen(sequence);
    int wordLen = strlen(word);
    
    if (wordLen < seqLen) {
        return false;
    }
    
    for (int i = 0; i < seqLen; i++) {
        char expectedKey = sequence[i];
        char actualChar = tolower(word[i]);
        
        bool found = false;
        
        for (int k = 2; k <= 9; k++) {
            if ((expectedKey - '0') == k) {
                const char* chars = keyMap[k];
                for (int c = 0; chars[c] != '\0'; c++) {
                    if (chars[c] == actualChar) {
                        found = true;
                        break;
                    }
                }
            }
        }
        
        if (!found) {
            return false;
        }
    }
    
    return true;
}

void T9Engine::multiTapInput(uint8_t key) {
    unsigned long currentTime = millis();
    
    if (key == lastKey && (currentTime - lastKeyTime) < 1000) {
        tapCount++;
        
        if (inputLength > 0) {
            inputLength--;
        }
    } else {
        tapCount = 0;
        lastKey = key;
    }
    
    lastKeyTime = currentTime;
    
    char c = getMultiTapChar(key, tapCount);
    
    if (inputLength < MAX_WORD_LENGTH - 1) {
        inputSequence[inputLength++] = c;
        inputSequence[inputLength] = '\0';
        strcpy(currentWord, inputSequence);
    }
}

char T9Engine::getMultiTapChar(uint8_t key, uint8_t tapCount) {
    if (key < '0' || key > '9') {
        return ' ';
    }
    
    int keyIndex = key - '0';
    const char* chars = keyMap[keyIndex];
    int numChars = strlen(chars);
    
    if (numChars == 0) {
        return ' ';
    }
    
    return chars[tapCount % numChars];
}

void T9Engine::loadDictionary() {
    // Dictionary is already loaded as const array
    Serial.println("T9 dictionary loaded");
}

bool T9Engine::isInDictionary(const char* word) {
    for (int i = 0; i < dictionarySize; i++) {
        if (strcasecmp(commonWords[i], word) == 0) {
            return true;
        }
    }
    return false;
}

bool T9Engine::addToUserDictionary(const char* word) {
    // User dictionary would be stored in EEPROM/SPIFFS
    return true;
}

void T9Engine::clearUserDictionary() {
    // Clear user dictionary from storage
}
