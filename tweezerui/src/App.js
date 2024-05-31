import React, { useState } from 'react';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTools } from '@fortawesome/free-solid-svg-icons';
import Hologram from './components/Hologram/Hologram';
import Bessel from './components/Bessel/Bessel';
import Settings from './components/Settings/Settings';
import DraggableWindow from './components/DraggableWindow/DraggableWindow';
import CameraPreview from './components/CameraPreview/CameraPreview'; 
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css'; // Bootstrap CSS




function App() {
  const [previewOpen, setPreviewOpen] = useState(false);

  const togglePreview = () => {
    setPreviewOpen(!previewOpen);
  };

  return (
  
    <div className="app container-fluid" style={{  height: '200vh' }}>
      <div className="row">
        <div className="col-3" style={{ minWidth: '200px', borderRight: '1px dashed lightgray', height:'100vh' }}>
          <Tabs>
            <TabList>
            <div className="form-check form-switch fs-5">
              <Tab>Hologram</Tab>
              <Tab>Bessel</Tab>
              </div>
            
            </TabList>

            <TabPanel>
              <Hologram />
            </TabPanel>
            <TabPanel>
              <Bessel />
            </TabPanel>
          </Tabs>
        </div>
        <div className="col-9" style={{ minWidth: '900px' }}>
          <CameraPreview />
          <button className={`floating-button ${previewOpen ? 'hidden' : ''}`} onClick={togglePreview}>
            <FontAwesomeIcon icon={faTools} />
          </button>

    

        </div>
      </div>
    </div>
   
  );
}

export default App;
