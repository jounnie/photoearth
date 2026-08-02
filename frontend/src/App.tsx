import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getPhotos } from './api/client'
import { AlbumPanel } from './components/AlbumPanel'
import { PhotoList } from './components/PhotoList'
import { MapView } from './components/MapView'
import type { Photo, GpsType } from './types'
import './App.css'

export default function App() {
  const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null)
  const [activePhoto, setActivePhoto]         = useState<Photo | null>(null)
  const [activeFilter, setActiveFilter]       = useState<GpsType | 'all'>('all')
  const [selectedIds, setSelectedIds]         = useState<Set<number>>(new Set())

  const { data: photos = [] } = useQuery({
    queryKey: ['photos', selectedAlbumId],
    queryFn: () => getPhotos(selectedAlbumId ?? undefined),
  })

  const handleFocusPhoto = (photo: Photo) => {
    setActivePhoto(prev => prev?.id === photo.id ? null : photo)
  }

  const handleToggleSelect = useCallback((photo: Photo, mode: 'single' | 'toggle' | 'range', allPhotos: Photo[]) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (mode === 'toggle') {
        if (next.has(photo.id)) next.delete(photo.id)
        else next.add(photo.id)
      } else if (mode === 'range') {
        // range from last selected to this photo (across flat list)
        const ids = allPhotos.map(p => p.id)
        const lastSelected = [...prev].findLast(id => ids.includes(id))
        if (lastSelected == null) {
          next.add(photo.id)
        } else {
          const a = ids.indexOf(lastSelected)
          const b = ids.indexOf(photo.id)
          const [lo, hi] = a < b ? [a, b] : [b, a]
          ids.slice(lo, hi + 1).forEach(id => next.add(id))
        }
      } else {
        // single: clear all, select just this one
        next.clear()
        next.add(photo.id)
      }
      return next
    })
  }, [])

  const handleClearSelection = useCallback(() => setSelectedIds(new Set()), [])

  return (
    <div className="app">
      <header className="app-header">
        <span>🌍</span>
        <h1>PhotoEarth</h1>
        {selectedIds.size > 0 && (
          <span className="selection-badge">{selectedIds.size} ausgewählt</span>
        )}
      </header>

      <div className="app-body">
        <AlbumPanel
          selectedAlbumId={selectedAlbumId}
          onSelect={id => { setSelectedAlbumId(id); setActivePhoto(null) }}
          onClearSelection={handleClearSelection}
        />

        <PhotoList
          photos={photos}
          activeId={activePhoto?.id ?? null}
          albumId={selectedAlbumId}
          activeFilter={activeFilter}
          selectedIds={selectedIds}
          onFilter={setActiveFilter}
          onFocus={handleFocusPhoto}
          onToggleSelect={handleToggleSelect}
          onClearSelection={handleClearSelection}
        />

        <MapView
          photos={photos}
          activePhoto={activePhoto}
          onMarkerClick={handleFocusPhoto}
        />
      </div>
    </div>
  )
}
