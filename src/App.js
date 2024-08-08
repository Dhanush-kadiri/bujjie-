import logo from './logo.svg';
import './App.css';
import { Router, Routes, Route } from 'react-router-dom';
import Default from './project/templates/Default';
import Login from './project/templates/Login';
import Signup from './project/templates/Signup';
import Home from './project/templates/Home';
import Profile from './project/templates/Profile';
import Content from './project/templates/Content';
import Reels from './project/templates/Reels';
import Video from './project/templates/Video';
import Post from './project/templates/Post';
import Editprofile from './project/templates/Editprofile';
import Otherprofile from './project/templates/Otherprofile';
import Message from './project/templates/Message';
import Uplodepost from './project/templates/Uplodepost';
import Uplodevideo from './project/templates/Uplodevideo';
import Uplodereels from './project/templates/Uplodereels';
import Settings from './project/templates/Settings';


function App() {
  return (

    <Router>

      <Routes>
        <Route path='/' element={<Default />} />
        <Route path='Login' element={<Login />} />
        <Route path='Signup' element={<Signup />} />
        <Route path='Home' element={<Home />} />
        <Route path='Profile' element={<Profile />} />
        <Route path='Content' element={<Content />} />
        <Route path='Reels' element={<Reels />} />
        <Route path='Video' element={<Video />} />
        <Route path='Post' element={<Post />} />
        <Route path='Editprofile' element={<Editprofile />} />
        <Route path='Otherprofile' element={<Otherprofile />} />
        <Route path='Message' element={<Message />} />
        <Route path='Uplodepost' element={<Uplodepost />} />
        <Route path='UplodeVideo' element={<Uplodevideo />} />
        <Route path='Uplodereels' element={<Uplodereels />} />
        <Route path='Settings' element={<Settings />} />
      </Routes>
    </Router>

  );
}

export default App;
