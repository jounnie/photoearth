import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { PinIcon } from './icons'
import type { Theme } from '../hooks/useTheme'
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

const ACCENT: Record<Theme, string> = { light: '#3f39ff', dark: '#7b74ff' }
const ACTIVE_COLOR = '#ff8c42'
const TILE_URL: Record<Theme, string> = {
  light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

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
  theme: Theme
}

export function MapView({ photos, activePhoto, onMarkerClick, theme }: Props) {
  const validPhotos = photos.filter(p => p.gps_type === 'ok')

  const iconDefault = useMemo(() => makeIcon(ACCENT[theme]), [theme])
  const iconActive  = useMemo(() => makeIcon(ACTIVE_COLOR), [])

  return (
    <MapContainer
      center={[20, 10]}
      zoom={2}
      style={{ flex: 1, minHeight: 0 }}
    >
      <TileLayer
        key={theme}
        url={TILE_URL[theme]}
        attribution='&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/">OSM</a>'
        maxZoom={19}
      />

      <FlyTo photo={activePhoto} />

      {validPhotos.map(photo => (
        <Marker
          key={photo.id}
          position={[photo.lat!, photo.lng!]}
          icon={activePhoto?.id === photo.id ? iconActive : iconDefault}
          eventHandlers={{ click: () => onMarkerClick(photo) }}
        >
          <Popup>
            <img
              src={`/api/photos/${photo.id}/image`}
              alt={photo.original_name}
              style={{ width: 160, height: 100, objectFit: 'cover', borderRadius: 4, display: 'block', marginBottom: 6 }}
            />
            <div className="popup-name">{photo.original_name}</div>
            {photo.location_name && (
              <div className="popup-location"><PinIcon /> {photo.location_name}</div>
            )}
            <div className="popup-coords">{photo.lat?.toFixed(6)}, {photo.lng?.toFixed(6)}</div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
