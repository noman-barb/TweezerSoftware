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
const mainServerURL = "http://10.0.63.153:4000";
const camServerURLs = {
  1: "http://10.0.63.153:4001",
  2: "http://10.0.63.153:4002"
};

function CameraPreview() {
  const [allCameras, setAllCameras] = useState([]);
  // const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  const canvasTrackRef = useRef(null);
  const canvasHologramRef = useRef(null);

  const {canvasRefs, imageProps, drawProps} = useGlobalContext();

  let drawing = false;

  const draw = (event) => {
    if (!drawing) return;
    const canvas = canvasHologramRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect(); // get the position of the canvas
  
    

    const x = event.clientX - drawProps.startX;
    const y = event.clientY - drawProps.startY;
  
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'red';
  
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const startDrawing = (event) => {
    drawing = true;
    draw(event);
  };

  const stopDrawing = () => {
    drawing = false;
    const canvas = canvasHologramRef.current;
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
  };

  useEffect(() => {
    const canvas = canvasHologramRef.current;
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    return () => {
      canvas.removeEventListener('mousedown', startDrawing);
      canvas.removeEventListener('mousemove', draw);
      canvas.removeEventListener('mouseup', stopDrawing);
      canvas.removeEventListener('mouseout', stopDrawing);
    };
  }, []);



  const [cameras, setCameras] = useState({
    1: {
      isPreviewActive: false,
      isStreaming: false,
      showModalSettings: false,
      isSwitchActive: true,
      formValues: {
        camId: 'Select Option',
        folderPath: 'F:/',
        targetFPS: '10',
        imageFormat: '',
        exposureTime: "10.0",
        gain: "1.0",
      },
      comment: "Select the camera ID from the dropdown list",
      isVirtual: false,
      fps: 0,
      rxSpeed: 0.0,
      isFirstImageReceived: false,
      canvasWidth: -1,
      canvasHeight: -1
    },
    2: {
      isPreviewActive: false,
      isStreaming: false,
      showModalSettings: false,
      isSwitchActive: true,
      formValues: {
        camId: 'Select Option',
        folderPath: 'F:/',
        targetFPS: '10',
        imageFormat: '',
        exposureTime: "10.0",
        gain: "1.0",
      },
      comment: "Select the camera ID from the dropdown list",
      isVirtual: false,
      fps: 0,
      rxSpeed: 0.0,
      isFirstImageReceived: false,
      canvasWidth: -1,
      canvasHeight: -1,
    }
  });

  let maxWidth = 1000;

  useEffect(() => {
    const fetchCameraDetails = async () => {
      if (cameras[1].showModalSettings || cameras[2].showModalSettings) {
        try {
          const response = await axios.get(camServerURLs[1] + "/get_all_camera_details");
          setAllCameras(response.data.data);
        } catch (error) {
          showToast("Error in fetching camera details", "error");
          showToast(error.message, "error");
        }
      }
    };

    fetchCameraDetails();
  }, [cameras[1].showModalSettings, cameras[2].showModalSettings]);


  // useEffect(() => {
  //   Object.values(canvasRefs).forEach((canvasRef, cameraId) => {
  //     if (canvasRef.current) {
  //       setCanvasSize(prevCanvasSize => ({
  //         ...prevCanvasSize,
  //         [cameraId]: {
  //           width: canvasRef.current.offsetWidth,
  //           height: canvasRef.current.offsetHeight,

  //         }
  //       }));
  //     }
  //   });
  // }, []);

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

  useEffect(() => {
    const canvas = canvasHologramRef.current;
    const context = canvas.getContext('2d');

    // Draw a hollow circle at x =100, y = 50
    context.beginPath();
    context.arc(150, 50, 20, 0, 2 * Math.PI);
    context.stroke();

  }, []);

  useEffect(() => {
    const updateCameraComment = (cameraId) => {
      const selectedCamera = allCameras.find((camera) => camera.camera_id === cameras[cameraId].formValues.camId);
      if (!selectedCamera) return;

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

  const handlePreviewToggle = async (cameraId) => {
    const isPreviewActive = cameras[cameraId].isPreviewActive;
    setCameras(prevCameras => ({
      ...prevCameras,
      [cameraId]: {
        ...prevCameras[cameraId],
        isSwitchActive: false,
      }
    }));

    const action = isPreviewActive ? 'Shutting down' : 'Warming up';
    let toastId = toast.loading(`${action} Cam ${cameraId} Server`, {
      position: "top-center",
      autoClose: 2000,
      theme: "dark",
      transition: Slide,
    });

    try {
      const endpoint = isPreviewActive ? '/stop_camera/' : `/warmup/camserver/${cameraId}`;
      const baseURL = isPreviewActive ? camServerURLs[cameraId] : mainServerURL; // Use main server for warming up
      const response = await axios[isPreviewActive ? 'post' : 'get'](baseURL + endpoint);

      setCameras(prevCameras => ({
        ...prevCameras,
        [cameraId]: {
          ...prevCameras[cameraId],
          isSwitchActive: true,
          isPreviewActive: !isPreviewActive,
          isStreaming: isPreviewActive ? false : prevCameras[cameraId].isStreaming,
        }
      }));

      toast.update(toastId, {
        render: response.data.msg,
        type: response.data.success ? "success" : "error",
        isLoading: false,
        autoClose: 2000,
      });
    } catch (error) {
      showToast(`Error in ${action.toLowerCase()} Cam Server ${cameraId}`, "error");
      showToast(error.message, "error");
    }
  };

  const handleStreamToggle = async (cameraId) => {
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
      position: "top-center",
      autoClose: 2000,
      theme: "dark",
      transition: Slide,
    });

    try {
      const endpoint = isStreaming ? 'stop_camera/' : 'start_camera/';
      const data = isStreaming ? {} : {
        camera_id: cameras[cameraId].formValues.camId,
        fps: cameras[cameraId].formValues.targetFPS,
        exposure_time: cameras[cameraId].formValues.exposureTime,
        gain: cameras[cameraId].formValues.gain,
        image_format: cameras[cameraId].formValues.imageFormat,
      };

      const response = await axios.post(camServerURLs[cameraId] + `/${endpoint}`, data);

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

      const ip = camServerURLs[cameraId].replace(/(^\w+:|^)\/\//, '');
      const websocket = new WebSocket("ws://" + ip + "/ws");
      webSocketConnections[cameraId] = websocket; // Store the connection
      websocket.binaryType = 'blob';

      const updateFpsAndSpeed = () => {
        console.log(frameCount, cameraId)

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

          drawProps.scale = scaleFactor;
          drawProps.centerX = canvas.width / 2;
          drawProps.centerY = canvas.height / 2;
          
          const rect = canvas.getBoundingClientRect();
          drawProps.startX = rect.left;
          drawProps.startY = rect.top;
          drawProps.endX = rect.right;
          drawProps.endY = rect.bottom;


          

          // set the height and width of the other two canvases
          canvasTrackRef.current.width = canvas.width;
          canvasTrackRef.current.height = canvas.height;
          canvasHologramRef.current.width = canvas.width;
          canvasHologramRef.current.height = canvas.height;


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
        <span className="me-3 fs-4 fw-bold" style={{ color: !isSwitchActive ? 'gray' : 'inherit' }}>
          Cam {cameraId}
        </span>

        <div className="form-check form-switch fs-5">
          <input
            className="form-check-input"
            type="checkbox"
            role="switch"
            disabled={!isSwitchActive}
            checked={isPreviewActive}
            onChange={() => handlePreviewToggle(cameraId)}
          />
        </div>

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

        {isStreaming && (
          <div className="d-flex justify-content-center" style={{ marginLeft: '30px' }}>
            <div>FPS: {fps.toFixed(2)} | Rx Speed: {(rxSpeed / 1024).toFixed(2)} Mb/s</div>
          </div>
        )}
      </div>
    );
  };

  const renderCameraModal = (cameraId) => {
    const { showModalSettings, formValues, comment, isVirtual } = cameras[cameraId];
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
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Gain</Form.Label>
              <Form.Control
                name="gain"
                type="number"
                step="0.01"
                placeholder="Enter gain"
                onChange={(e) => handleInputChange(e, cameraId)}
                value={formValues.gain}
              />
            </Form.Group>


            <Form.Group className="mb-3">
              <Form.Label>Image Format</Form.Label>
              <Form.Select name="imageFormat" onChange={(e) => handleInputChange(e, cameraId)} value={formValues.imageFormat}>
                <option value="compressed">Compressed</option>
                <option value="original">Original</option>
              </Form.Select>
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
            opacity: 1.0,
            zIndex: 1,
            backgroundColor: 'transparent',
          }}
        />
        <canvas
          ref={canvasRefs[2]}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 1.0,
            zIndex: 2,
            backgroundColor: 'transparent',
          }}
        />

        <canvas
          ref={canvasTrackRef}
          style={{
            gridArea: '1 / 1 / 2 / 2',
            opacity: 1.0,
            zIndex: 3,
            backgroundColor: 'transparent',


          }}
        />

        <canvas
          ref={canvasHologramRef}
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