import React, { useState, useEffect } from 'react';
import { Modal, Button, Space, Typography, Tag, Spin, message } from 'antd';
import { 
  LeftOutlined, 
  RightOutlined, 
  ZoomInOutlined, 
  ZoomOutOutlined,
  FullscreenOutlined,
  TagsOutlined,
  FileImageOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { logInfo, logError } from '../../../utils/professional_logger';

const { Text, Title } = Typography;

const ReleaseImageViewerModal = ({ 
  visible, 
  onClose, 
  images, 
  currentIndex, 
  onIndexChange,
  releaseId,
  annotations = {},
  classMapping = {},
  showAnnotations = true
}) => {
  const [loading, setLoading] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showAnnotationOverlay, setShowAnnotationOverlay] = useState(showAnnotations);

  const currentImage = images[currentIndex];
  
  // Use same key-matching logic as thumbnails
  const imageAnnotations = currentImage ? (() => {
    const { path, filename, fullPath } = currentImage;
    // Handle both forward and backward slashes for cross-platform compatibility
    const normalizedPath = path.replace(/\\/g, '/');
    const backslashPath = path.replace(/\//g, '\\');
    const possibleKeys = [path, filename, fullPath, normalizedPath, backslashPath];
    
    for (const key of possibleKeys) {
      if (annotations[key]) {
        console.log(`✅ Modal found annotations for image using key: ${key}`, annotations[key]);
        return annotations[key];
      }
    }
    
    console.log(`❌ Modal: No annotations found for any key variant:`, possibleKeys);
    return [];
  })() : [];

  useEffect(() => {
    setImageLoaded(false);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [currentIndex]);

  useEffect(() => {
    setShowAnnotationOverlay(showAnnotations);
  }, [showAnnotations]);

  const handlePrevious = () => {
    if (currentIndex > 0) {
      onIndexChange(currentIndex - 1);
      logInfo('app.frontend.ui', 'image_viewer_previous', 'Previous image clicked', {
        timestamp: new Date().toISOString(),
        currentIndex: currentIndex - 1,
        totalImages: images.length
      });
    }
  };

  const handleNext = () => {
    if (currentIndex < images.length - 1) {
      onIndexChange(currentIndex + 1);
      logInfo('app.frontend.ui', 'image_viewer_next', 'Next image clicked', {
        timestamp: new Date().toISOString(),
        currentIndex: currentIndex + 1,
        totalImages: images.length
      });
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev / 1.2, 0.1));
  };

  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && zoom > 1) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      handlePrevious();
    } else if (e.key === 'ArrowRight') {
      handleNext();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  useEffect(() => {
    if (visible) {
      document.addEventListener('keydown', handleKeyDown);
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [visible, currentIndex, isDragging, dragStart, pan]);

  if (!currentImage) {
    return null;
  }

  const fullImageUrl = `http://localhost:12000/api/v1/releases/${releaseId}/file/${currentImage.path}`;

  return (
    <Modal
      title={
        <Space>
          <FileImageOutlined />
          <span>{currentImage.filename}</span>
          <Tag color={getSplitColor(currentImage.split)}>
            {currentImage.split.toUpperCase()}
          </Tag>
          {imageAnnotations.length > 0 && (
            <Tag color="red">
              {imageAnnotations.length} annotation{imageAnnotations.length !== 1 ? 's' : ''}
            </Tag>
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="90vw"
      style={{ top: 20 }}
      footer={[
        <Space key="controls" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button 
              icon={<LeftOutlined />} 
              onClick={handlePrevious}
              disabled={currentIndex === 0}
            >
              Previous
            </Button>
            <Text>
              {currentIndex + 1} of {images.length}
            </Text>
            <Button 
              icon={<RightOutlined />} 
              onClick={handleNext}
              disabled={currentIndex === images.length - 1}
            >
              Next
            </Button>
          </Space>
          
          <Space>
            <Button
              icon={<TagsOutlined />}
              type={showAnnotationOverlay ? "primary" : "default"}
              onClick={() => setShowAnnotationOverlay(!showAnnotationOverlay)}
            >
              {showAnnotationOverlay ? 'Hide' : 'Show'} Annotations
            </Button>
            <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} disabled={zoom <= 0.1} />
            <Text style={{ minWidth: '60px', textAlign: 'center' }}>
              {Math.round(zoom * 100)}%
            </Text>
            <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} disabled={zoom >= 5} />
            <Button icon={<FullscreenOutlined />} onClick={handleResetZoom}>
              Reset
            </Button>
          </Space>
        </Space>
      ]}
    >
      <div style={{ 
        height: '70vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        overflow: 'hidden',
        position: 'relative',
        backgroundColor: '#f5f5f5',
        cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default'
      }}>
        {loading && (
          <div style={{ position: 'absolute', zIndex: 10 }}>
            <Spin size="large" />
          </div>
        )}
        
        <div
          style={{
            position: 'relative',
            transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
            transition: isDragging ? 'none' : 'transform 0.2s ease'
          }}
          onMouseDown={handleMouseDown}
        >
          <img
            src={fullImageUrl}
            alt={currentImage.filename}
            style={{
              maxWidth: '100%',
              maxHeight: '70vh',
              objectFit: 'contain',
              display: imageLoaded ? 'block' : 'none'
            }}
            onLoad={(e) => {
              setImageLoaded(true);
              setLoading(false);
              // Store image dimensions for annotation calculations
              window.modalImageWidth = e.target.naturalWidth;
              window.modalImageHeight = e.target.naturalHeight;
              console.log(`🔍 Modal image loaded: ${window.modalImageWidth}x${window.modalImageHeight}`);
              logInfo('app.frontend.ui', 'modal_image_loaded', 'Modal image loaded successfully', {
                timestamp: new Date().toISOString(),
                filename: currentImage.filename,
                releaseId: releaseId,
                imagePath: currentImage.path
              });
            }}
            onError={(e) => {
              setLoading(false);
              logError('app.frontend.ui', 'modal_image_load_failed', 'Modal image failed to load', {
                timestamp: new Date().toISOString(),
                filename: currentImage.filename,
                releaseId: releaseId,
                imagePath: currentImage.path,
                error: e.message || 'Image load error'
              });
              message.error(`Failed to load image: ${currentImage.filename}`);
            }}
            onLoadStart={() => {
              setLoading(true);
            }}
            draggable={false}
          />
          
          {/* Annotation Overlay */}
          {showAnnotationOverlay && imageLoaded && imageAnnotations.length > 0 && (
            <svg
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none'
              }}
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
            >
              {imageAnnotations.map((annotation, annIndex) => {
                const { class_id, bbox, polygon, segmentation, type } = annotation;
                const className = classMapping[class_id] || `Class ${class_id}`;
                const color = getClassColor(class_id);
                
                // Handle polygon annotations (flat array format)
                if (polygon && Array.isArray(polygon) && polygon.length > 0) {
                  // Convert flat array [x1, y1, x2, y2, ...] to points
                  const points = [];
                  for (let i = 0; i < polygon.length; i += 2) {
                    if (i + 1 < polygon.length) {
                      points.push({ x: polygon[i], y: polygon[i + 1] });
                    }
                  }
                  
                  if (points.length > 0) {
                    // Convert polygon points to SVG path
                    const pathData = points.map((point, index) => {
                      const x = point.x * 100; // Convert to percentage
                      const y = point.y * 100;
                      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
                    }).join(' ') + ' Z'; // Close the path
                    
                    // Calculate centroid for text placement
                    const centroidX = points.reduce((sum, p) => sum + p.x, 0) / points.length * 100;
                    const centroidY = points.reduce((sum, p) => sum + p.y, 0) / points.length * 100;
                    
                    return (
                      <g key={annIndex}>
                        <path
                          d={pathData}
                          fill={color}
                          fillOpacity="0.1"
                          stroke={color}
                          strokeWidth="0.5"
                          opacity="0.8"
                        />
                        <text
                          x={centroidX}
                          y={centroidY}
                          fill={color}
                          fontSize="3"
                          fontWeight="bold"
                          textAnchor="middle"
                          dominantBaseline="middle"
                        >
                          {className}
                        </text>
                      </g>
                    );
                  }
                }
                
                // Handle segmentation annotations (point objects)
                if (type === 'polygon' && segmentation && Array.isArray(segmentation)) {
                  // Convert polygon points to SVG path
                  const pathData = segmentation.map((point, index) => {
                    const x = (point.x / 1) * 100; // Assuming normalized coordinates
                    const y = (point.y / 1) * 100;
                    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
                  }).join(' ') + ' Z'; // Close the path
                  
                  // Calculate centroid for text placement
                  const centroidX = segmentation.reduce((sum, p) => sum + p.x, 0) / segmentation.length * 100;
                  const centroidY = segmentation.reduce((sum, p) => sum + p.y, 0) / segmentation.length * 100;
                  
                  return (
                    <g key={annIndex}>
                      <path
                        d={pathData}
                        fill={color}
                        fillOpacity="0.1"
                        stroke={color}
                        strokeWidth="0.5"
                        opacity="0.8"
                      />
                      <text
                        x={centroidX}
                        y={centroidY}
                        fontSize="3"
                        fill={color}
                        fontWeight="bold"
                        textAnchor="middle"
                        style={{ textShadow: '0 0 2px rgba(255,255,255,0.8)' }}
                      >
                        {className}
                      </text>
                    </g>
                  );
                }
                
                // Handle bounding box annotations
                if (bbox && Array.isArray(bbox) && bbox.length >= 4) {
                  // YOLO format: [center_x, center_y, width, height]
                  const [center_x, center_y, width, height] = bbox;
                  
                  // Convert to corner format: [x, y, width, height]  
                  const x = center_x - width/2;
                  const y = center_y - height/2;
                  
                  // Check if coordinates are normalized (0-1) or pixel values
                  const imageWidth = window.modalImageWidth || 1;
                  const imageHeight = window.modalImageHeight || 1;
                  console.log(`🔍 BBOX DEBUG: YOLO [${center_x}, ${center_y}, ${width}, ${height}] → Corner [${x}, ${y}, ${width}, ${height}], imageSize: ${imageWidth}x${imageHeight}`);
                  const isNormalized = center_x <= 1 && center_y <= 1 && width <= 1 && height <= 1;
                  console.log(`🔍 BBOX isNormalized: ${isNormalized}`);
                  
                  let rectX, rectY, rectWidth, rectHeight;
                  if (isNormalized) {
                    // Normalized coordinates (0-1) - convert to percentages
                    rectX = x * 100;
                    rectY = y * 100;
                    rectWidth = width * 100;
                    rectHeight = height * 100;
                  } else {
                    // Pixel coordinates - convert to percentages based on image size
                    rectX = (x / imageWidth) * 100;
                    rectY = (y / imageHeight) * 100;
                    rectWidth = (width / imageWidth) * 100;
                    rectHeight = (height / imageHeight) * 100;
                  }
                  
                  return (
                    <g key={annIndex}>
                      {/* Bounding box */}
                      <rect
                        x={rectX}
                        y={rectY}
                        width={rectWidth}
                        height={rectHeight}
                        fill={color}
                        fillOpacity="0.1"
                        stroke={color}
                        strokeWidth="0.5"
                        opacity="0.8"
                      />
                      {/* Class label background */}
                      <rect
                        x={rectX}
                        y={Math.max(0, rectY - 4)}
                        width={className.length * 1.2 + 2}
                        height="4"
                        fill={color}
                        opacity="0.8"
                      />
                      {/* Class label text */}
                      <text
                        x={rectX + 1}
                        y={Math.max(2.5, rectY - 0.5)}
                        fontSize="2.5"
                        fill="white"
                        fontWeight="bold"
                      >
                        {className}
                      </text>
                    </g>
                  );
                }
                
                // Return null for unsupported annotation types
                return null;
              })}
            </svg>
          )}
        </div>
      </div>
      
      {/* Image Metadata */}
      <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#fafafa', borderRadius: '6px' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Space>
            <Text strong>File:</Text>
            <Text code>{currentImage.filename}</Text>
          </Space>
          <Space>
            <Text strong>Split:</Text>
            <Tag color={getSplitColor(currentImage.split)}>
              {currentImage.split.toUpperCase()}
            </Tag>
          </Space>
          <Space>
            <Text strong>Path:</Text>
            <Text type="secondary">{currentImage.path}</Text>
          </Space>
          {imageAnnotations.length > 0 && (
            <Space>
              <Text strong>Annotations:</Text>
              <Space wrap>
                {imageAnnotations.map((annotation, index) => {
                  const className = classMapping[annotation.class_id] || `Class ${annotation.class_id}`;
                  return (
                    <Tag key={index} color={getClassColor(annotation.class_id)} size="small">
                      {className}
                    </Tag>
                  );
                })}
              </Space>
            </Space>
          )}
        </Space>
      </div>
    </Modal>
  );
};

// Helper function to get split color
const getSplitColor = (split) => {
  switch (split?.toLowerCase()) {
    case 'train': return 'blue';
    case 'val': case 'valid': return 'orange';
    case 'test': return 'red';
    default: return 'default';
  }
};

// Helper function to get class color
const getClassColor = (classId) => {
  const colors = [
    '#ff4d4f', '#1890ff', '#52c41a', '#faad14', '#722ed1',
    '#eb2f96', '#13c2c2', '#fa541c', '#a0d911', '#2f54eb'
  ];
  return colors[classId % colors.length];
};

export default ReleaseImageViewerModal;