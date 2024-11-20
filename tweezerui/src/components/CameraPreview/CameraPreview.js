import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCog } from '@fortawesome/free-solid-svg-icons';
import 'bootstrap/dist/css/bootstrap.min.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Slide } from 'react-toastify';
import axios from 'axios';
import { useGlobalContext } from '../../GlobalContext';



function CameraPreview() {
  const [allCameras, setAllCameras] = useState([]);
  // const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });


  const { canvasRefs, imageProps, setImageProps, drawProps, setDrawProps, serverInfo, cameras, setCameras } = useGlobalContext();

  let drawing = false;

 



  const [maxWidth, setMaxWidth] = useState(1456);







  useEffect(() => {
    // set timeout to send request to /heartbeat of both the servers and it controls the is_preview and is switch active
    // if the server is not responding, is_preview is false, is_switch_active is true



    const fetchHeartbeat = (cameraId) => {


      const baseURL = "http://" + serverInfo.camserver[cameraId].ip + ":" + serverInfo.camserver[cameraId].portHTTP;
      
      const endpoint = '/heartbeat';

      const api = baseURL + endpoint;

     


      axios.get(api)
        .then((response) => {


          setCameras(prevCameras => ({
            ...prevCameras,
            [cameraId]: {
              ...prevCameras[cameraId],
              isPreviewActive: true
            }
          }));

        })
        .catch((error) => {
          setCameras(prevCameras => ({
            ...prevCameras,
            [cameraId]: {
              ...prevCameras[cameraId],
              isPreviewActive: false
            }
          }));


        });
    };

    setInterval(() => {
      fetchHeartbeat(1);
      fetchHeartbeat(2);
    }, 2000);




  }, []);



  useEffect(() => {
    const fetchCameraDetails = async () => {
      if (cameras[1].showModalSettings || cameras[2].showModalSettings) {
        try {
          const baseURL =   "http://" +   serverInfo.camserver[1].ip + ":" + serverInfo.camserver[1].portHTTP;
          const response = await axios.get(baseURL+ "/get_all_camera_details");
          throwErrorIfNotSuccess(response, null);


          setAllCameras(response.data.data);
        } catch (error) {
          showToast("Error in fetching camera details", "error");
          showToast(error.message, "error");
        }
      }
    };

    fetchCameraDetails();
  }, [cameras[1].showModalSettings, cameras[2].showModalSettings]);



  const handleInputChange = (event, cameraId) => {

    setCameras(prevCameras => ({
      ...prevCameras,
      [cameraId]: {
        ...prevCameras[cameraId],
        formValues: {
          ...prevCameras[cameraId].formValues,
          [event.target.name]: event.target.value,
        },
      }
    }));
  };

  // useEffect(() => {
  //   const canvas = canvasRefs[4].current;
  //   const context = canvas.getContext('2d');

  //   // Draw a hollow circle at x =100, y = 50
  //   context.beginPath();
  //   context.arc(150, 50, 20, 0, 2 * Math.PI);
  //   context.stroke();

  // }, []);

  useEffect(() => {
    const updateCameraComment = (cameraId) => {
      const selectedCamera = allCameras.find((camera) => camera.camera_id === cameras[cameraId].formValues.camId);
      if (!selectedCamera) {
        setCameras(prevCameras => ({
          ...prevCameras,
          [cameraId]: {
            ...prevCameras[cameraId],
            comment: "Select a camera",
            isVirtual: true,
          }
        }));

        return
      };

      const isVirtual = !selectedCamera.details.is_real;
      let comment = selectedCamera.details.comment;
      comment = comment + " | " + (isVirtual ? "Virtual Camera" : "Real Camera");

      setCameras(prevCameras => ({
        ...prevCameras,
        [cameraId]: {
          ...prevCameras[cameraId],
          comment: comment,
          isVirtual: isVirtual,
        }
      }));
    };

    updateCameraComment(1);
    updateCameraComment(2);
  }, [cameras[1].formValues.camId, cameras[2].formValues.camId, allCameras]);

  const showToast = (msg, type, delay = 2000) => {
    toast[type](msg, {
      position: "bottom-right",
      autoClose: delay,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      progress: undefined,
      theme: "dark",
      transition: Slide,
    });
  };

  const throwErrorIfNotSuccess = (response, toastId) => {

    const success = response.data.success;
    // raise error is success is false with response message
    if (!success) {


      if (toastId) {
        toast.update(toastId, {
          render: response.data.msg,
          type: "error",
          isLoading: false,
          autoClose: 1000,
        });
      }
      throw new Error(response.data.msg);
    }



  };


  const handleStreamToggle = async (cameraId) => {


    // check if min max values are respected
    const formValues = cameras[cameraId].formValues;

    let error = false;

    if (formValues.targetFPS < cameras[cameraId].formValuesMinMax.targetFPS.min || formValues.targetFPS > cameras[cameraId].formValuesMinMax.targetFPS.max) {
      showToast(`Target FPS must be between ${cameras[cameraId].formValuesMinMax.targetFPS.min} and ${cameras[cameraId].formValuesMinMax.targetFPS.max}`, "error");
      error = true;
    }

    if (formValues.exposureTime < cameras[cameraId].formValuesMinMax.exposureTime.min || formValues.exposureTime > cameras[cameraId].formValuesMinMax.exposureTime.max) {
      showToast(`Exposure Time must be between ${cameras[cameraId].formValuesMinMax.exposureTime.min} and ${cameras[cameraId].formValuesMinMax.exposureTime.max}`, "error");
      error = true;

    }

    if (formValues.gain < cameras[cameraId].formValuesMinMax.gain.min || formValues.gain > cameras[cameraId].formValuesMinMax.gain.max) {
      showToast(`Gain must be between ${cameras[cameraId].formValuesMinMax.gain.min} and ${cameras[cameraId].formValuesMinMax.gain.max}`, "error");
      error = true;
    }

    if (error) return;




    const isStreaming = cameras[cameraId].isStreaming;
    setCameras(prevCameras => ({
      ...prevCameras,
      [cameraId]: {
        ...prevCameras[cameraId],
        isSwitchActive: false,
      }
    }));

    const action = isStreaming ? 'Stopping' : 'Starting';
    let toastId = toast.loading(`${action} ${cameras[cameraId].formValues.camId}`, {
      position: "bottom-center",
      autoClose: 2000,
      theme: "dark",
      transition: Slide,
    });

    try {
      const endpoint = isStreaming ? '/stop_camera/' : '/start_camera/';
      const data = isStreaming ? {} : {
        camera_id: cameras[cameraId].formValues.camId,
        fps: cameras[cameraId].formValues.targetFPS,
        exposure_time: cameras[cameraId].formValues.exposureTime,
        gain: cameras[cameraId].formValues.gain,
        image_format: cameras[cameraId].formValues.imageFormat,
        folder_path: cameras[cameraId].formValues.folderPath,
        request_locate: cameras[cameraId].formValues.requestLocate
      };

      const baseURL = "http://" +  serverInfo.camserver[cameraId].ip + ":" + serverInfo.camserver[cameraId].portHTTP;
      const response = await axios.post(baseURL + endpoint, data);

      throwErrorIfNotSuccess(response, toastId);

      setCameras(prevCameras => ({
        ...prevCameras,
        [cameraId]: {
          ...prevCameras[cameraId],
          isSwitchActive: true,
          isStreaming: !isStreaming,
        }
      }));

      toast.update(toastId, {
        render: response.data.msg,
        type: response.data.success ? "success" : "error",
        isLoading: false,
        autoClose: 2000,
      });
    } catch (error) {

      // revert the camera switch to active
      setCameras(prevCameras => ({
        ...prevCameras,
        [cameraId]: {
          ...prevCameras[cameraId],
          isSwitchActive: true,
        }
      }));


      showToast(`Error in ${action.toLowerCase()} camera ${cameraId}`, "error");
      showToast(error.message, "error");
    }
  };

  useEffect(() => {

    const webSocketConnections = {}; // Store WebSocket connections

    const connectToWebSocket = (cameraId) => {


      if (!cameras[cameraId].isPreviewActive || webSocketConnections[cameraId]) return;

      let frameCount = 0;
      let dataCount = 0;
      let firstImageReceived = false;

      const baseURL = serverInfo.camserver[cameraId].ip + ":" + serverInfo.camserver[cameraId].portWS;

      const websocket = new WebSocket("ws://" + baseURL + "/ws");
      webSocketConnections[cameraId] = websocket; // Store the connection
      websocket.binaryType = 'blob';

      const updateFpsAndSpeed = () => {
       

        // set the fps and speed for the camera
        const copyFrameCount = frameCount;
        const copyDataCount = dataCount;


        setCameras(prevCameras => ({
          ...prevCameras,
          [cameraId]: {
            ...prevCameras[cameraId],
            fps: copyFrameCount,
            rxSpeed: copyDataCount / 1024,
          }
        }));

        frameCount = 0;
        dataCount = 0;
      };

      const intervalId = setInterval(updateFpsAndSpeed, 1000);

      const img = new Image();
      img.onload = () => {
        const canvas = canvasRefs[cameraId].current;
        const ctx = canvas.getContext('2d');
        if (!firstImageReceived) {


          // now apply the rule that max width is 1000
          const scaleFactor = maxWidth / img.width;
          canvas.width = img.width * scaleFactor;
          canvas.height = img.height * scaleFactor;
          firstImageReceived = true;

          setCameras(prevCameras => ({
            ...prevCameras,
            [cameraId]: {
              ...prevCameras[cameraId],
              isFirstImageReceived: true,
              canvasWidth: canvas.width,
              canvasHeight: canvas.height,
            }

          }));



          imageProps.width = img.width;
          imageProps.height = img.height;

          setImageProps({
            width: img.width,
            height: img.height
          });

          drawProps.scale = scaleFactor;
          drawProps.centerX = canvas.width / 2;
          drawProps.centerY = canvas.height / 2;

          const rect = canvas.getBoundingClientRect();
          drawProps.startX = rect.left;
          drawProps.startY = rect.top;
          drawProps.endX = rect.right;
          drawProps.endY = rect.bottom;


          // set the height and width of the other two canvases
          canvasRefs[3].current.width = canvas.width;
          canvasRefs[3].current.height = canvas.height;
          canvasRefs[4].current.width = canvas.width;
          canvasRefs[4].current.height = canvas.height;

          // since i changed the values manually, i need to update the context by calling setDrawProps
          // i set the values directly because I want the effect to be instant and not wait for the next render
          setDrawProps({
            scale: scaleFactor,
            centerX: canvas.width / 2,
            centerY: canvas.height / 2,
            startX: rect.left,
            startY: rect.top,
            endX: rect.right,
            endY: rect.bottom
          });




        }
        ctx.drawImage(img, 0, 0, img.width, img.height, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(img.src);
      };

      websocket.onmessage = (event) => {

        const url = URL.createObjectURL(event.data);
        img.src = url;
        frameCount++;
        dataCount += event.data.size;
      };

      websocket.onopen = () => console.log(`Connected to Cam Server ${cameraId}`);
      websocket.onerror = (error) => console.error('WebSocket error:', error);
      websocket.onclose = () => {
        console.log(`Disconnected from Cam Server ${cameraId}`);
        clearInterval(intervalId);
        delete webSocketConnections[cameraId]; // Remove connection from the object
      };
    };

    connectToWebSocket(1);
    connectToWebSocket(2);

    // Clean up WebSocket connections when component unmounts
    return () => {
      Object.values(webSocketConnections).forEach(ws => ws.close());
    };

  }, [cameras[1].isPreviewActive, cameras[2].isPreviewActive]);


  const renderCameraControls = (cameraId) => {

    const { isPreviewActive, isStreaming, showModalSettings, isSwitchActive, formValues, comment, isVirtual, fps, rxSpeed } = cameras[cameraId];
    const handleModalToggle = () => setCameras(prevCameras => ({
      ...prevCameras,
      [cameraId]: {
        ...prevCameras[cameraId],
        showModalSettings: !prevCameras[cameraId].showModalSettings,
      }
    }));

    return (
      <div className="d-flex justify-content-center justify-content-center align-items-center" key={cameraId}>


        <span className="d-flex align-items-center me-3 fs-4 fw-bold" style={{ color: !isSwitchActive ? 'gray' : 'inherit' }}>
          Cam {cameraId}
          <div style={{
            height: '10px',
            width: '10px',
            backgroundColor: isPreviewActive ? 'green' : 'red',
            borderRadius: '50%',
            display: 'inline-block',
            marginLeft: '5px'
          }}></div>
        </span>



        {/* <div className="form-check form-switch fs-5">
        //   <input
        //     className="form-check-input"
        //     type="checkbox"
        //     role="switch"
        //     disabled={!isSwitchActive}
        //     checked={isPreviewActive}
        //     onChange={() => handlePreviewToggle(cameraId)}
        //   />
        // </div> */}

        <div className="d-flex justify-content-center" style={{ marginLeft: '30px' }}>
          <div className="btn-group">
            <Button variant="primary" onClick={handleModalToggle} disabled={!isPreviewActive || !isSwitchActive || isStreaming}>
              <FontAwesomeIcon icon={faCog} />
            </Button>
            <Button
              variant="primary"
              onClick={() => handleStreamToggle(cameraId)}
              disabled={!isPreviewActive || !isSwitchActive}
              style={{ backgroundColor: isStreaming ? 'orange' : '' }}
            >
              {isStreaming ? 'Stop Stream' : 'Start Stream'}
            </Button>
          </div>
        </div>

        {1 == 1 && (
          <div className="d-flex justify-content-center" style={{ marginLeft: '30px' }}>
            <div>FPS: {fps.toFixed(2)} | Rx Speed: {(rxSpeed / 1024).toFixed(2)} Mb/s</div>
          </div>
        )}
      </div>
    );
  };

  const renderCameraModal = (cameraId) => {
    const { showModalSettings, formValues, comment, isVirtual, formValuesMinMax } = cameras[cameraId];
    const handleCloseModal = () => setCameras(prevCameras => ({
      ...prevCameras,
      [cameraId]: {
        ...prevCameras[cameraId],
        showModalSettings: false,
      }
    }));

    return (

      <Modal show={showModalSettings} onHide={handleCloseModal} key={cameraId}>
        <Modal.Header closeButton>
          <Modal.Title>Cam Server {cameraId} Configuration</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Camera ID</Form.Label>
              <Form.Select name="camId" onChange={(e) => handleInputChange(e, cameraId)} value={formValues.camId}>
                <option value="">Select Option</option>
                {allCameras.map((camera, index) => (
                  <option key={index} value={camera.camera_id}>
                    {camera.camera_id}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                {comment}
              </Form.Text>
            </Form.Group>
            {isVirtual && (
              <Form.Group className="mb-3">
                <Form.Label>Folder Path</Form.Label>
                <Form.Control name="folderPath" placeholder="Enter folder path" onChange={(e) => handleInputChange(e, cameraId)} value={formValues.folderPath} />
              </Form.Group>
            )}
            <Form.Group className="mb-3">
              <Form.Label>Target Streaming FPS</Form.Label>
              <Form.Control name="targetFPS" type="number" placeholder="Enter FPS" onChange={(e) => handleInputChange(e, cameraId)} value={formValues.targetFPS} />
              {formValues.targetFPS < formValuesMinMax.targetFPS.min || formValues.targetFPS > formValuesMinMax.targetFPS.max ? (
                <Form.Text style={{ color: 'red' }}>
                  Value must be between {formValuesMinMax.targetFPS.min} and {formValuesMinMax.targetFPS.max}
                </Form.Text>
              ) : null}
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Exposure Time (ms)</Form.Label>
              <Form.Control
                name="exposureTime"
                type="number"
                step="0.01"
                placeholder="Enter exposure time in ms"
                onChange={(e) => handleInputChange(e, cameraId)}
                value={formValues.exposureTime}
              />
              {formValues.exposureTime < formValuesMinMax.exposureTime.min || formValues.exposureTime > formValuesMinMax.exposureTime.max ? (
                <Form.Text style={{ color: 'red' }}>
                  Value must be between {formValuesMinMax.exposureTime.min} and {formValuesMinMax.exposureTime.max}
                </Form.Text>
              ) : null}
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Gain</Form.Label>
              <Form.Control
                name="gain"
                type="number"
                step="0.01"
                min="0"
                max="100"
                placeholder="Enter gain"
                onChange={(e) => handleInputChange(e, cameraId)}
                value={formValues.gain}
              />
              {formValues.gain < formValuesMinMax.gain.min || formValues.gain > formValuesMinMax.gain.max ? (
                <Form.Text style={{ color: 'red' }}>
                  Value must be between {formValuesMinMax.gain.min} and {formValuesMinMax.gain.max}
                </Form.Text>
              ) : null}
            </Form.Group>


            <Form.Group className="mb-3">
              <Form.Label>Image Format</Form.Label>
              <Form.Select name="imageFormat" onChange={(e) => handleInputChange(e, cameraId)} value={formValues.imageFormat}>
                <option value="compressed">Compressed</option>
                <option value="original">Original</option>
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              {cameras[cameraId].canRequestLocate && (
                <Form.Check
                  type="checkbox"
                  label="Request Locate"
                  onChange={(e) => {
                    setCameras(prevCameras => ({
                      ...prevCameras,
                      [cameraId]: {
                        ...prevCameras[cameraId],
                        formValues: {
                          ...prevCameras[cameraId].formValues,
                          requestLocate: e.target.checked
                        }
                      }
                    }));
                  }}
                  checked={formValues.requestLocate}
                />
              )}
            </Form.Group>
          </Form>
        </Modal.Body>
      </Modal>
    );
  };




  return (
    <div className="p-3">
      <div className="d-flex flex-row justify-content-between">
        {[1, 2].map(cameraId => renderCameraControls(cameraId))}
      </div>
      {/* <div className="mt-3">
        <Form.Range 
          min={500} 
          max={5000} 
          step={100} 
          value={maxWidth} 
        
        />
        <span className="ms-2">Zoom:</span>
      </div> */}

      <div style={{
        display: 'grid',
        width: '100%',
        height: '100%',
        marginTop: '20px',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        placeItems: 'center'
      }}>
        <canvas
          ref={canvasRefs[1]}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 0.5,
            zIndex: 1,
            backgroundColor: 'transparent',
          }}
        />
        <canvas
          ref={canvasRefs[2]}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 0.5,
            zIndex: 2,
            backgroundColor: 'transparent',
          }}
        />

        <canvas
          ref={canvasRefs[3]}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 1.0,
            zIndex: 3,
            backgroundColor: 'transparent',


          }}
        />

        <canvas
          ref={canvasRefs[4]}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 1.0,
            zIndex: 4,
            backgroundColor: 'transparent'

          }}
        />
      </div>

      {[1, 2].map(cameraId => renderCameraModal(cameraId))}

      <ToastContainer />
    </div>
  );
}

export default CameraPreview;