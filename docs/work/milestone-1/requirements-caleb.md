# Folio Requirements Document — Caleb's Half

## Functional Requirements

### Data & Storage

- **F18.** The system shall allow the student to manually create a coursework record that includes, at a minimum, a course, an assignment name, and a due date.
- **F19.** The system shall allow the student to edit a manually entered coursework record after it has been created.
- **F20.** The system shall allow the student to delete a coursework record.
- **F21.** The system shall validate manually entered coursework before saving the coursework record.
- **F22.** The system shall reject a manually entered coursework record when the course or assignment name is blank, or the due date is missing or does not match the date format specified by the manual-entry interface.
- **F23.** The system shall identify each field that prevents a manually entered coursework record from being saved.
- **F24.** The system shall allow the student to import coursework from a CSV file that contains the required Folio coursework fields.
- **F25.** The system shall validate each CSV record before saving the imported coursework record.
- **F26.** The system shall reject a CSV record that omits a required field or contains a value that does not conform to the data type or format specified for that field by the CSV import interface.
- **F27.** For each rejected CSV record, the system shall report the record's location in the CSV file and each reason for rejection.
- **F28.** The system shall reject a CSV file that cannot be parsed or does not contain the required columns without adding any records from that file.
- **F29.** The system shall treat two CSV records as duplicates when all required coursework fields have identical values and shall add no more than one of those records during a single CSV import.
- **F30.** The system shall import every valid CSV record when other records in the same CSV file are invalid.
- **F31.** The system shall persist coursework records, academic plans, scheduled tasks, and game and reward state across application sessions.
- **F32.** The system shall restore the student's most recently saved coursework records, academic plans, scheduled tasks, and game and reward state when the student begins a subsequent application session.
- **F33.** The system shall preserve each association between a scheduled task and the coursework record or academic plan to which it belongs.

### Scheduling & Conflicts

- **F34.** The system shall display scheduled tasks from multiple academic plans in a combined schedule.
- **F35.** The system shall preserve scheduled tasks from separate academic plans as distinct records in the combined schedule.
- **F36.** The system shall detect a scheduling conflict when one scheduled task starts before another scheduled task ends and ends after the other scheduled task starts.
- **F37.** The system shall notify the student when creating or rescheduling a scheduled task causes a scheduling conflict with an existing scheduled task.
- **F38.** The system shall identify every scheduled task involved in a detected scheduling conflict.
- **F39.** The system shall allow the student to resolve a scheduling conflict by rescheduling at least one of the conflicting tasks.
- **F40.** The system shall update the combined schedule when the date or time of a scheduled task changes.
- **F41.** The system shall remove a scheduled task from the combined schedule when the student deletes it from their academic plan.

### Game & Reward Correctness

- **F42.** The system shall count a scheduled task toward academic plan progress only while it is marked complete.
- **F43.** When a scheduled task with an associated reward changes from incomplete to complete, the system shall award the associated reward no more than once for that status transition.
- **F44.** The system shall update the progress of an academic plan when the completion status of a scheduled task in that plan changes.
- **F45.** The system shall calculate an academic plan's progress using only the scheduled tasks that belong to that academic plan.
- **F46.** The system shall not modify coursework records when game or reward data changes.
- **F47.** The system shall exclude game and reward data from academic information prepared for sharing with an instructor.
- **F48.** Disabling the game and reward features shall not delete or alter the student's academic plans, coursework records, or scheduled tasks.

### Independent Planning

- **F49.** The system shall allow the student to create and save an academic plan without sharing information with an instructor.
- **F50.** The system shall allow the student to modify and complete an academic plan without instructor feedback.
- **F51.** The system shall allow the student to schedule, reschedule, and complete scheduled tasks without instructor participation.
- **F52.** The absence of instructor feedback shall not prevent the student from viewing an existing academic plan.

## Interface Requirements

- **I6.** The system shall accept coursework imports in CSV format.
- **I7.** The CSV import interface shall identify all required columns and the accepted data format for each column before the student initiates an import.
- **I8.** After processing a CSV import, the system shall display the number of accepted and rejected CSV records.
- **I9.** For each rejected CSV record, the CSV import interface shall display the record's location in the file and each validation error.
- **I10.** The scheduling interface shall display the associated course or academic plan name for each scheduled task in the combined schedule.
- **I11.** The scheduling interface shall display a conflict indicator on each scheduled task involved in a detected scheduling conflict.
- **I12.** The manual-entry interface shall provide a labeled input control for each field required to create a valid coursework record.
- **I13.** The manual-entry interface shall specify the accepted date format for a coursework record's due date.
- **I14.** When the system rejects a manually entered coursework record, the manual-entry interface shall identify each field that caused the rejection and explain the applicable validation rule.

## Performance Requirements

> **TODO:** Define the acceptance-test environment, network conditions, and representative dataset sizes for P1–P5. We cannot reliably reproduce the following thresholds until the test conditions are specified.

- **P1.** The system shall display the requested stored academic plan within 2 seconds of the student submitting the request.
- **P2.** The system shall update the displayed schedule within 2 seconds of the student creating, modifying, or deleting a scheduled task.
- **P3.** The system shall detect and display all scheduling conflicts within 2 seconds of the student adding or rescheduling a task.
- **P4.** The system shall import and validate a CSV file containing 500 coursework records within 5 seconds after the student initiates the import.
- **P5.** The system shall confirm that it has saved a change to a coursework record, academic plan, or scheduled task within 2 seconds of the student submitting the change.
