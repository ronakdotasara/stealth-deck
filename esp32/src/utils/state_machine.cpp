/**
 * ============================================================================
 * state_machine.cpp - State Machine Implementation
 * ============================================================================
 */

#include "state_machine.h"

// ============================================================================
// CONSTRUCTOR
// ============================================================================

StateMachine::StateMachine() :
    _stateCount(0),
    _currentState(STATE_IDLE),
    _previousState(STATE_IDLE),
    _historyIndex(0),
    _stateEnterTime(0)
{
    memset(_states, 0, sizeof(_states));
    memset(_stateHistory, 0, sizeof(_stateHistory));
}

// ============================================================================
// INITIALIZATION
// ============================================================================

void StateMachine::begin() {
    Serial.println("State Machine initialized");
    _stateEnterTime = millis();
}

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

bool StateMachine::addState(StateID id, const char* name,
                            StateCallback onEnter,
                            StateCallback onExit,
                            StateCallback onUpdate,
                            unsigned long timeout) {
    if (_stateCount >= MAX_STATES) {
        Serial.println("ERROR: State machine full!");
        return false;
    }
    
    _states[_stateCount].id = id;
    _states[_stateCount].name = name;
    _states[_stateCount].onEnter = onEnter;
    _states[_stateCount].onExit = onExit;
    _states[_stateCount].onUpdate = onUpdate;
    _states[_stateCount].timeout = timeout;
    
    _stateCount++;
    
    return true;
}

bool StateMachine::transitionTo(StateID newState) {
    if (newState == _currentState) {
        return true; // Already in this state
    }
    
    State* currentStateObj = findState(_currentState);
    State* newStateObj = findState(newState);
    
    if (!newStateObj) {
        Serial.printf("ERROR: State %d not found!\n", newState);
        return false;
    }
    
    Serial.printf("State transition: %s -> %s\n",
                  currentStateObj ? currentStateObj->name : "UNKNOWN",
                  newStateObj->name);
    
    // Call exit callback of current state
    if (currentStateObj && currentStateObj->onExit) {
        currentStateObj->onExit();
    }
    
    // Update state
    _previousState = _currentState;
    _currentState = newState;
    _stateEnterTime = millis();
    
    // Add to history
    addToHistory(newState);
    
    // Call enter callback of new state
    if (newStateObj->onEnter) {
        newStateObj->onEnter();
    }
    
    return true;
}

void StateMachine::update() {
    State* currentStateObj = findState(_currentState);
    
    if (!currentStateObj) {
        return;
    }
    
    // Call update callback
    if (currentStateObj->onUpdate) {
        currentStateObj->onUpdate();
    }
    
    // Check for timeout
    if (currentStateObj->timeout > 0) {
        unsigned long stateTime = millis() - _stateEnterTime;
        if (stateTime >= currentStateObj->timeout) {
            Serial.printf("State %s timed out after %lu ms\n",
                         currentStateObj->name, stateTime);
            // Could trigger a timeout transition here
        }
    }
}

// ============================================================================
// GETTERS
// ============================================================================

StateID StateMachine::getPreviousState() const {
    return _previousState;
}

const char* StateMachine::getCurrentStateName() const {
    State* state = const_cast<StateMachine*>(this)->findState(_currentState);
    return state ? state->name : "UNKNOWN";
}

unsigned long StateMachine::getStateTime() const {
    return millis() - _stateEnterTime;
}

// ============================================================================
// DEBUG
// ============================================================================

void StateMachine::printState() const {
    State* state = const_cast<StateMachine*>(this)->findState(_currentState);
    
    Serial.println("\n===== STATE MACHINE =====");
    Serial.printf("Current State: %s (ID: %d)\n",
                  state ? state->name : "UNKNOWN", _currentState);
    Serial.printf("Time in State: %lu ms\n", getStateTime());
    Serial.printf("Previous State: %d\n", _previousState);
    Serial.println("========================\n");
}

void StateMachine::printHistory() const {
    Serial.println("\n===== STATE HISTORY =====");
    for (int i = 0; i < MAX_STATE_HISTORY; i++) {
        if (_stateHistory[i] != 0) {
            Serial.printf("%d. State ID: %d\n", i + 1, _stateHistory[i]);
        }
    }
    Serial.println("=========================\n");
}

// ============================================================================
// PRIVATE METHODS
// ============================================================================

State* StateMachine::findState(StateID id) {
    for (uint8_t i = 0; i < _stateCount; i++) {
        if (_states[i].id == id) {
            return &_states[i];
        }
    }
    return nullptr;
}

void StateMachine::addToHistory(StateID state) {
    _stateHistory[_historyIndex] = state;
    _historyIndex = (_historyIndex + 1) % MAX_STATE_HISTORY;
}
