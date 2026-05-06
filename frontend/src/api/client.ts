import axios from 'axios'
import type { Photo, Album } from '../types'

const api = axios.create({ baseURL: '/api' })

// Photos
export const getPhotos = (albumId?: number) =>
  api.get<Photo[]>('/photos', { params: albumId != null ? { album_id: albumId } : {} }).then(r => r.data)

export const uploadPhotos = (files: File[], albumId?: number) => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  if (albumId != null) form.append('album_id', String(albumId))
  return api.post<Photo[]>('/photos/upload', form).then(r => r.data)
}

export const updateGps = (id: number, lat: number, lng: number, locationName?: string) =>
  api.patch<Photo>(`/photos/${id}/gps`, { lat, lng, location_name: locationName }).then(r => r.data)

export const assignAlbum = (id: number, albumId: number | null) =>
  api.patch<Photo>(`/photos/${id}/album`, null, { params: { album_id: albumId } }).then(r => r.data)

export const deletePhoto = (id: number) =>
  api.delete(`/photos/${id}`)

export const detectLocation = (id: number) =>
  api.post<Photo>(`/ai/${id}/detect-location`).then(r => r.data)

export const imageUrl = (filename: string) => `/api/photos/by-filename/${filename}/image`
export const photoImageUrl = (id: number) => `/api/photos/${id}/image`

// Albums
export const getAlbums = () =>
  api.get<Album[]>('/albums').then(r => r.data)

export const createAlbum = (name: string, description = '') =>
  api.post<Album>('/albums', { name, description }).then(r => r.data)

export const updateAlbum = (id: number, data: { name?: string; description?: string }) =>
  api.patch<Album>(`/albums/${id}`, data).then(r => r.data)

export const deleteAlbum = (id: number) =>
  api.delete(`/albums/${id}`)
