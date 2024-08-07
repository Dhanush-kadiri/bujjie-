import logo from './logo.svg';
import './App.css';
import {  Router,Routes, Route } from 'react-router-dom';
import Hello from './project/templates/hello'


function App() {
  return (
   <>
<Router>

<Routes>

    <Route path='/' element= { < Hello/> }  />

</Routes>

</Router>
   </>
  );
}

export default App;
