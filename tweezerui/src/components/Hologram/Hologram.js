import React, { useEffect, useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css'; // Ensure Bootstrap CSS is imported
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';
import { Collapse, CardBody, Card } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons';
import { Button, Form } from 'react-bootstrap';
import { useGlobalContext } from '../../GlobalContext';
import TrackBar from './TrackOption';

function Hologram() {
    
    const { trackOptions, setTrackOptions } = useGlobalContext();


    return (<div>

        <TrackBar trackOptions={trackOptions} setTrackOptions={setTrackOptions} />
    </div>);
    

}

export default Hologram;