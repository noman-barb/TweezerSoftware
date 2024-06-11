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
import Heater from './ObjectiveHeater';
import SLMOptions from './SLMOptions'

function Hologram() {

    const { trackOptions, setTrackOptions } = useGlobalContext();


    return (
        <div className="container">
            <div className="row mb-3 mt-3">
                <TrackBar
                    trackOptions={trackOptions}
                    setTrackOptions={setTrackOptions}
                />
            </div>
            <div className="row  mb-3">
                <Heater />
            </div>
            <div className="row  mb-3">
                <SLMOptions />
            </div>
        </div>
    );

}

export default Hologram;