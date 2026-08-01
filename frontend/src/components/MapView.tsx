import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Photo } from '../types'

const makeIcon = (color: string) =>
  L.divIcon({
    className: '',
    html: `<svg width="28" height="36" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 0C6.27 0 0 6.27 0 14c0 9.75 14 22 14 22S28 23.75 28 14C28 6.27 21.73 0 14 0z" fill="${color}"/>
      <circle cx="14" cy="14" r="6" fill="white"/>
    </svg>`,
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
  })

const ICON_DEFAULT = makeIcon('#6c8fff')
const ICON_ACTIVE  = makeIcon('#ff8c42')

function FlyTo({ photo }: { photo: Photo | null }) {
  const map = useMap()
  useEffect(() => {
    if (photo?.lat != null && photo?.lng != null) {
      map.flyTo([photo.lat, photo.lng], Math.max(map.getZoom(), 13), { animate: true, duration: 0.8 })
    }
  }, [photo, map])
  return null
}

interface Props {
  photos: Photo[]
  activePhoto: Photo | null
  onMarkerClick: (p: Photo) => void
}

export function MapView({ photos, activePhoto, onMarkerClick }: Props) {
  const validPhotos = photos.filter(p => p.gps_type === 'ok')

  return (
    <MapContainer
      center={[20, 10]}
      zoom={2}
      style={{ flex: 1, minHeight: 0 }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/">OSM</a>'
        maxZoom={19}
      />

      <FlyTo photo={activePhoto} />

      {validPhotos.map(photo => (
        <Marker
          key={photo.id}
          position={[photo.lat!, photo.lng!]}
          icon={activePhoto?.id === photo.id ? ICON_ACTIVE : ICON_DEFAULT}
          eventHandlers={{ click: () => onMarkerClick(photo) }}
        >
          <Popup>
            <img
              src={`/api/photos/${photo.id}/image`}
              alt={photo.original_name}
              style={{ width: 160, height: 100, objectFit: 'cover', borderRadius: 6, display: 'block', marginBottom: 6 }}
            />
            <div style={{ fontWeight: 600 }}>{photo.original_name}</div>
            {photo.location_name && <div style={{ fontSize: '0.78rem', color: '#aaa' }}>📍 {photo.location_name}</div>}
            <div style={{ fontSize: '0.73rem', color: '#888' }}>{photo.lat?.toFixed(6)}, {photo.lng?.toFixed(6)}</div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
