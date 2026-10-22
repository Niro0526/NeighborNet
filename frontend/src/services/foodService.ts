import { FoodListing, FoodListingStatus } from '../types';
import { mockRepository } from './mockRepository';
import { apiClient, isApiMode, getAllPages } from './apiClient';
import { adaptFoodListing } from './apiAdapters';

export const foodService = {
  /**
   * Fetches active food listings.
   */
  async getFoodListings(): Promise<FoodListing[]> {
    if (!isApiMode()) {
      return mockRepository.getFoodListings();
    }

    const rawList = await getAllPages('/resources/');
    return rawList.map(adaptFoodListing).sort((a, b) => b.createdAt.localeCompare(a.createdAt) || b.id.localeCompare(a.id));
  },

  /**
   * Retrieves single food listing by ID.
   */
  async getListingById(id: string): Promise<FoodListing | undefined> {
    if (!isApiMode()) {
      const listings = mockRepository.getFoodListings();
      return listings.find((l) => l.id === id);
    }

    try {
      const res = await apiClient.get(`/resources/${id}/`);
      return adaptFoodListing(res.data);
    } catch {
      return undefined;
    }
  },

  /**
   * Fetches listings registered by a specific provider organization.
   */
  async getListingsByProvider(providerId: string): Promise<FoodListing[]> {
    if (!isApiMode()) {
      const listings = mockRepository.getFoodListings();
      return listings.filter((l) => l.providerId === providerId);
    }

    const all = await this.getFoodListings();
    return all.filter((l) => l.providerId === providerId);
  },

  /**
   * Listings for the signed-in food provider (membership-aware).
   */
  async getMyListings(options?: { providerIds?: string[]; providerName?: string }): Promise<FoodListing[]> {
    const all = await this.getFoodListings();
    const ids = options?.providerIds?.filter(Boolean) || [];
    if (ids.length > 0) {
      return all.filter((listing) => ids.includes(String(listing.providerId)));
    }
    const name = options?.providerName?.trim().toLowerCase();
    if (name) {
      return all.filter((listing) => listing.providerName.toLowerCase().includes(name));
    }
    return isApiMode() ? [] : all;
  },

  /**
   * Persists a new surplus food listing to PostgreSQL.
   */
  async createListing(
    listingData: Omit<FoodListing, 'id' | 'createdAt' | 'status'>
  ): Promise<FoodListing> {
    if (!isApiMode()) {
      const newListing: FoodListing = {
        ...listingData,
        id: `FOOD-${Date.now().toString().slice(-4)}`,
        status: 'available',
        createdAt: new Date().toISOString(),
      };
      mockRepository.addFoodListing(newListing);
      return newListing;
    }

    const payload = {
      name: listingData.name,
      category: String(listingData.category || 'cooked_meals').toLowerCase().replace(/[\s-]/g, '_'),
      quantity: Number(listingData.quantity),
      unit: listingData.unit || 'kg',
      unit_weight_kg: listingData.unitWeightKg ?? null,
      pickupStart: listingData.pickupStart,
      pickupEnd: listingData.pickupEnd,
      pickupAddress: listingData.pickupAddress,
      pickupLatitude: listingData.pickupLatitude,
      pickupLongitude: listingData.pickupLongitude,
      safeUntil: listingData.safeUntil,
      storageRequirements: listingData.storageRequirements || 'Ambient',
      dietaryTags: listingData.dietaryTags || [],
      safetyNotes: listingData.safetyNotes || '',
      isDisasterRelief: Boolean(listingData.isDisasterRelief),
      disasterEventId: listingData.disasterEventId || null,
    };

    const res = await apiClient.post('/resources/', payload);
    return adaptFoodListing(res.data);
  },

  async updateListing(
    id: string,
    listingData: Partial<Omit<FoodListing, 'id' | 'createdAt' | 'status' | 'providerId' | 'providerName' | 'locationId'>>
  ): Promise<FoodListing> {
    if (!isApiMode()) {
      mockRepository.updateFoodListing(id, listingData);
      const updated = mockRepository.getFoodListings().find((listing) => listing.id === id);
      if (!updated) throw new Error('Listing not found');
      return updated;
    }

    const payload: Record<string, unknown> = {};
    if (listingData.name !== undefined) payload.name = listingData.name;
    if (listingData.category !== undefined) {
      payload.category = String(listingData.category).toLowerCase().replace(/[\s-]/g, '_');
    }
    if (listingData.quantity !== undefined) payload.quantity = Number(listingData.quantity);
    if (listingData.unit !== undefined) payload.unit = listingData.unit;
    if (listingData.unitWeightKg !== undefined) payload.unit_weight_kg = listingData.unitWeightKg;
    if (listingData.pickupStart !== undefined) payload.pickupStart = listingData.pickupStart;
    if (listingData.pickupEnd !== undefined) payload.pickupEnd = listingData.pickupEnd;
    if (listingData.pickupAddress !== undefined) payload.pickupAddress = listingData.pickupAddress;
    if (listingData.pickupLatitude !== undefined) payload.pickupLatitude = listingData.pickupLatitude;
    if (listingData.pickupLongitude !== undefined) payload.pickupLongitude = listingData.pickupLongitude;
    if (listingData.safeUntil !== undefined) payload.safeUntil = listingData.safeUntil;
    if (listingData.storageRequirements !== undefined) payload.storageRequirements = listingData.storageRequirements;
    if (listingData.dietaryTags !== undefined) payload.dietaryTags = listingData.dietaryTags;
    if (listingData.safetyNotes !== undefined) payload.safetyNotes = listingData.safetyNotes;

    const res = await apiClient.patch(`/resources/${id}/`, payload);
    return adaptFoodListing(res.data);
  },

  /**
   * Withdraws a surplus listing from circulation.
   */
  async withdrawListing(id: string): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateFoodListing(id, { status: 'expired' });
      return;
    }

    await apiClient.post(`/resources/${id}/withdraw/`);
  },

  /**
   * Backward compatibility for updating listing status.
   */
  async updateListingStatus(id: string, status: FoodListingStatus): Promise<void> {
    if (!isApiMode()) {
      mockRepository.updateFoodListing(id, { status });
      return;
    }

    if (status === 'expired') {
      await this.withdrawListing(id);
    }
  },
};

export default foodService;
