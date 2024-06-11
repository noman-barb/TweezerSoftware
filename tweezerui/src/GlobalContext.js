import React, {useEffect, createContext, useRef, useState, useContext } from 'react';


const GlobalContext = createContext({ canvas1: null, canvas2: null });

export const useGlobalContext = () => {
  return useContext(GlobalContext);
};

export const CanvasProvider = ({ children }) => {

  const canvasRefs = {
    1: useRef(null),
    2: useRef(null),
    3 : useRef(null),
    4 : useRef(null),
  };

  const [imageProps, setImageProps] = useState({
    "width": -1,
    "height": -1,
  });

  const [drawProps, setDrawProps] = useState({
    "scale": 1,
    "startX": 1,
    "startY": 1,
    "endX": 1,
    "endY": 1,
    "centerX": 1,
    "centerY": 1
  });

  const localStorageIDs = {
    "cameras": "cameras",
    "cameraserver": "cameraserver",
    "trackoptions": "trackoptions",
    "heatoptions": "heatoptions",
    "slmOptions": "slmOptions",
  }

  const [serverInfo, setServerInfo] = useState({
    "camserver": {
      1: { "ip": "10.0.63.153", "portHTTP": "4001", "username": "", "password": "" , "portWS": "4003" },
      2: { "ip": "10.0.63.153", "portHTTP": "4002", "username": "", "password": "" , "portWS": "4004" }
    },
    "trackserver": {
      1: { "ip": "10.0.63.153", "portHTTP": "4011", "username": "", "password": "", "portWS": "4012" },
    },
    "heaterserver": {
      1: { "ip": "10.0.63.153", "portHTTP": "4031", "username": "", "password": "", "portWS": "4031" },
    }
  });


  /////////////////////////////////////////////////////////////////////////////////////////////////////
  // Camera State

  const [cameras, setCameras] = useState(() => {
    // Load initial camera state from localStorage
    const storedCameras = JSON.parse(localStorage.getItem(localStorageIDs.camera)) || {};
    return {
      1: {
        isPreviewActive: false,
        isStreaming: false,
        showModalSettings: false,
        isSwitchActive: true,
        canRequestLocate: true,
        formValues: {
          camId: storedCameras[1]?.formValues?.camId || 'Select Option',
          folderPath: storedCameras[1]?.formValues?.folderPath || 'F:/',
          targetFPS: storedCameras[1]?.formValues?.targetFPS || '10',
          imageFormat: storedCameras[1]?.formValues?.imageFormat || '',
          exposureTime: storedCameras[1]?.formValues?.exposureTime || "10.0",
          gain: storedCameras[1]?.formValues?.gain || "1.0",
          requestLocate: storedCameras[1]?.formValues?.requestLocate || false,
        },
        formValuesMinMax:{
          exposureTime: { min: 0.0, max: 2000.0 },
          gain: { min: 0.0, max: 100.0 },
          targetFPS: { min: 0.1, max: 30 }

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
        canRequestLocate: true,
        formValues: {
          camId: storedCameras[2]?.formValues?.camId || 'Select Option',
          folderPath: storedCameras[2]?.formValues?.folderPath || 'F:/',
          targetFPS: storedCameras[2]?.formValues?.targetFPS || '10',
          imageFormat: storedCameras[2]?.formValues?.imageFormat || '',
          exposureTime: storedCameras[2]?.formValues?.exposureTime || "10.0",
          gain: storedCameras[2]?.formValues?.gain || "1.0",
          requestLocate: storedCameras[2]?.formValues?.requestLocate || false,
        },
        formValuesMinMax:{
          exposureTime: { min: 0.0, max: 2000.0 },
          gain: { min: 0.0, max: 100.0 },
          targetFPS: { min: 0.1, max: 30 }

        },
        comment: "Select the camera ID from the dropdown list",
        isVirtual: false,
        fps: 0,
        rxSpeed: 0.0,
        isFirstImageReceived: false,
        canvasWidth: -1,
        canvasHeight: -1,
      }
    };
  });
  // Save camera state to localStorage
  useEffect(() => {
    localStorage.setItem(localStorageIDs.camera, JSON.stringify(cameras));
  }, [cameras]);




  /////////////////////////////////////////////////////////////////////////////////////////////////////


  /////////////////////////////////////////////////////////////////////////////////////////////////////
  // Track Options State

  const [trackOptions, setTrackOptions] = useState(() => {
    // Load initial camera state from localStorage
    const storedTrackOptions = JSON.parse(localStorage.getItem(localStorageIDs.trackoptions)) || {};
    
    return {
      receiveStream: false,
      isOnline: false,
      isOpenTrackOption:  storedTrackOptions.isOpenTrackOption || false,
      diameter: storedTrackOptions.diameter || 21,
      seperation: storedTrackOptions.seperation || 18,
      percentile: storedTrackOptions.percentile || 1,
      minmass: storedTrackOptions.minmass || 31000,
      maxmass: storedTrackOptions.maxmass || 99999,
      pixelThresh: storedTrackOptions.pixelThresh || 10,
      preprocess: storedTrackOptions.preprocess || false,
      lshort: storedTrackOptions.lshort || 0,
      llong: storedTrackOptions.llong || 23,
      minEcc: storedTrackOptions.minEcc || 0,
      maxEcc: storedTrackOptions.maxEcc || 99,
      refine: storedTrackOptions.refine || 1,
      gridX: storedTrackOptions.gridX || 500,
      gridY: storedTrackOptions.gridY || 500,
      overlap: storedTrackOptions.overlap || 100,
      
    };
  });

  const [trackOptionsMinMaxVals, setTrackOptionsMinMaxVals] = useState({

    diameter: { min: 5, max: 120 },
    seperation: { min: 5, max: 120 },
    percentile: { min: 1, max: 100 },
    minmass: { min: -1, max: 100000 },
    maxmass: { min: -1, max: 100000 },
    pixelThresh: { min: -1, max: 100 },
    lshort: { min: -1, max: 100 },
    llong: { min: 1, max: 100 },
    minEcc: { min: -1, max: 100 },
    maxEcc: { min: -1, max: 100 },
    refine: { min: 1, max: 100 },
    gridX: { min: 200, max: 3000 },
    gridY: { min: 200, max: 1000 },
    overlap: { min: 1, max: 100 }
  });



  // Save camera state to localStorage
  useEffect(() => {
    
    localStorage.setItem(localStorageIDs.trackoptions, JSON.stringify(trackOptions));
}, [trackOptions]);

  /////////////////////////////////////////////////////////////////////////////////////////////////////


  ///////////////// heater state /////////////////

  // const [heater, setHeater] = useState({
  //   objectiveTemperature: -1,
  //   setPoint: -1,
  //   setPointSetAt: 20.0,
  //   isHeaterServiceOnline: false,
  //   minSetPoint: 17.5,
  //   maxSetPoint: 36.0,
  //   isCollapsed: false,
  // });

  const [heater, setHeater] = useState(() => {
    // Load initial camera state from localStorage
    const storedHeater = JSON.parse(localStorage.getItem(localStorageIDs.heatoptions)) || {};
    return {
      objectiveTemperature: -1,
      setPoint: -1,
      setPointSetAt: storedHeater.setPointSetAt || 20.0,
      isHeaterServiceOnline: false,
      minSetPoint: 17.5,
      maxSetPoint: 36.0,
      isCollapsed: storedHeater.isCollapsed || false,
      timeSeriesSetPoints: null,
      timeSeriesObjectiveTemperatures: null,
      timeSeriesTimes: null,
      lastUpdated: null
    };
  }
  );

  // save the heater state to local storage on change of isCollapsed
  useEffect(() => {
    localStorage.setItem(localStorageIDs.heatoptions, JSON.stringify(heater));
  }, [heater.isCollapsed]);





  /////////////////////////////////////////////////////////////////////////////////////////////////////
  ///////   Hologram options //////////////////////////////////////////////////////////////////////////

  const [slmOptions, setSLMOptions] = useState(() => {
    // Load initial camera state from localStorage
    const storedSLMOptions = JSON.parse(localStorage.getItem(localStorageIDs.slmOptions)) || {};


    
    return {
      isCollapsed: storedSLMOptions.isCollapsed || false,
      isOnline: false,
      isAffineCollapsed : false,
      affine: {
        SLM_X_0: 10,
        SLM_Y_0: 10,
        CAM_X_0: 10,
        CAM_Y_0: 10,
        SLM_X_1: -20,
        SLM_Y_1: -20,
        CAM_X_1: -20,
        CAM_Y_1: -20,
        SLM_X_2: -30,
        SLM_Y_2: 10,
        CAM_X_2: -30,
        CAM_Y_2: 10,
        ...storedSLMOptions.affine
      },
      points:{
        xArray: [],
        yArray: [],
        zArray: [],
        intensityArray: [],
        ...storedSLMOptions.points
      }
  
      
    };
  });


  // save the hologram options to local storage on change of isCollapsed
  useEffect(() => {
    localStorage.setItem(localStorageIDs.slmOptions, JSON.stringify(slmOptions));
  }, [slmOptions]);




  ///////////////////////////////////////







  return (
    <GlobalContext.Provider value={{ canvasRefs, 
    imageProps, setImageProps, 
    drawProps, setDrawProps, 
    localStorageIDs, serverInfo, setServerInfo, 
    cameras, setCameras,
    trackOptions, setTrackOptions   ,
    trackOptionsMinMaxVals,
    heater, setHeater,
    slmOptions, setSLMOptions
    }}>
      {children}
    </GlobalContext.Provider>
  );
};
