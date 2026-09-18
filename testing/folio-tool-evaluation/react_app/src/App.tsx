import { FormEvent, useState } from "react";

type Priority = "Low" | "Medium" | "High";
type Assignment = { name: string; dueDate: string; priority: Priority };

const today = new Date().toLocaleDateString("en-CA");

export default function App() {
  const [name, setName] = useState("");
  const [dueDate, setDueDate] = useState(today);
  const [priority, setPriority] = useState<Priority>("Low");
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [error, setError] = useState("");

  function addAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedName = name.trim();

    if (!trimmedName) {
      setError("Assignment name is required.");
      return;
    }

    setAssignments((current) => [
      ...current,
      { name: trimmedName, dueDate, priority },
    ]);
    setName("");
    setError("");
  }

  return (
    <main>
      <h1>Folio Prototype</h1>
      <form onSubmit={addAssignment} noValidate>
        <label>
          Assignment Name
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label>
          Due Date
          <input
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
        </label>
        <label>
          Priority
          <select
            value={priority}
            onChange={(event) => setPriority(event.target.value as Priority)}
          >
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
        </label>
        <button type="submit">Add Assignment</button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      <h2>Assignments</h2>
      {assignments.length ? (
        <table>
          <thead>
            <tr><th>Assignment</th><th>Due Date</th><th>Priority</th></tr>
          </thead>
          <tbody>
            {assignments.map((assignment, index) => (
              <tr key={`${assignment.name}-${index}`}>
                <td>{assignment.name}</td>
                <td>{assignment.dueDate}</td>
                <td>{assignment.priority}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No assignments added.</p>
      )}
    </main>
  );
}
