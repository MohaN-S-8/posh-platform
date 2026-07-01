import "./App.css";

const App = () => {
  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h1>POSH Training Platform</h1>
      <p>
        Frontend is running. Backend API:{" "}
        <a href="http://localhost:8000/docs">http://localhost:8000/docs</a>
      </p>
    </div>
  );
};

export default App;
