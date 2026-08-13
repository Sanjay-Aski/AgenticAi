# Deterministic Tutor Lab Record – Experiment 1

## AIM

To design and implement a deterministic tutoring agent that answers predefined academic and government-scheme questions using rule-based logic and fixed templates, ensuring repeatable outputs for identical inputs.

## DOP / DOS

* **DOP (Date of Performance):** 6 August 2026
* **DOS (Date of Submission):** 13 August 2026

## What Implemented

* Deterministic question-answering engine using keyword-based intent detection.
* JSON-based knowledge templates for predefined academic and government-scheme questions.
* Fixed response templates to ensure consistent and repeatable answers.
* Default fallback response when the requested information is not available.

## Conclusion

The deterministic tutor core was successfully implemented using rule-based intent detection and fixed response templates. The system provides consistent, predictable, and explainable responses for predefined questions, while also handling unknown queries through a fixed fallback response.

## Additional Optimizations Implemented

### Optimization 2: Intent Classification

* Added a rule-based learning-intent classifier in the tutoring agent.
* Detects whether a query asks for: Definition, Algorithm, Complexity Analysis, Example, Comparison, Code Generation, or Debugging.
* Applies an intent-specific prompt contract deterministically.

### Optimization 8: Adaptive Tutoring

* Added a learner-level selector in the Streamlit UI: Beginner, Intermediate, Advanced.
* The tutor formats response depth and style based on selected level.
* Deterministic property is preserved for identical question + level input.
