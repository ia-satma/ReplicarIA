/**
 * Custom React Query hooks for ReplicarIA API.
 * Provides automatic caching, refetching, and loading states.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/services/api";

// =============================================================================
// PROJECTS
// =============================================================================

/**
 * Hook for fetching all projects with caching.
 */
export function useProjects(params = {}) {
    return useQuery({
        queryKey: ["projects", params],
        queryFn: () => api.projects.list(params),
        staleTime: 60000, // 1 minute
    });
}

/**
 * Hook for fetching a single project.
 */
export function useProject(id) {
    return useQuery({
        queryKey: ["project", id],
        queryFn: () => api.projects.get(id),
        enabled: !!id,
    });
}

/**
 * Hook for creating a project with cache invalidation.
 */
export function useCreateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data) => api.projects.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
        },
    });
}

/**
 * Hook for updating a project with cache invalidation.
 */
export function useUpdateProject() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }) => api.projects.update(id, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["projects"] });
            queryClient.invalidateQueries({ queryKey: ["project", variables.id] });
        },
    });
}

// =============================================================================
// AGENTS
// =============================================================================

/**
 * Hook for fetching all agents.
 */
export function useAgents() {
    return useQuery({
        queryKey: ["agents"],
        queryFn: () => api.agents.list(),
        staleTime: 300000, // 5 minutes - agents rarely change
    });
}

/**
 * Hook for fetching a single agent.
 */
export function useAgent(id) {
    return useQuery({
        queryKey: ["agent", id],
        queryFn: () => api.agents.get(id),
        enabled: !!id,
        staleTime: 300000,
    });
}

/**
 * Hook for agent analysis with mutation.
 */
export function useAgentAnalyze() {
    return useMutation({
        mutationFn: ({ id, data }) => api.agents.analyze(id, data),
    });
}

// =============================================================================
// DEFENSE FILES
// =============================================================================

/**
 * Hook for fetching all defense files.
 */
export function useDefenseFiles(params = {}) {
    return useQuery({
        queryKey: ["defense-files", params],
        queryFn: () => api.get("/api/defense-files", { params }),
        staleTime: 30000,
    });
}

/**
 * Hook for fetching a single defense file.
 */
export function useDefenseFile(id) {
    return useQuery({
        queryKey: ["defense-file", id],
        queryFn: () => api.get(`/api/defense-files/${id}`),
        enabled: !!id,
    });
}

// =============================================================================
// EMPRESAS
// =============================================================================

/**
 * Hook for fetching all empresas.
 */
export function useEmpresas() {
    return useQuery({
        queryKey: ["empresas"],
        queryFn: () => api.empresas.list(),
        staleTime: 120000, // 2 minutes
    });
}

/**
 * Hook for fetching a single empresa.
 */
export function useEmpresa(id) {
    return useQuery({
        queryKey: ["empresa", id],
        queryFn: () => api.empresas.get(id),
        enabled: !!id,
        staleTime: 120000,
    });
}

// =============================================================================
// UTILITY HOOKS
// =============================================================================

/**
 * Hook to get the query client for manual cache operations.
 */
export function useInvalidateQueries() {
    const queryClient = useQueryClient();

    return {
        invalidateProjects: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
        invalidateAgents: () => queryClient.invalidateQueries({ queryKey: ["agents"] }),
        invalidateDefenseFiles: () => queryClient.invalidateQueries({ queryKey: ["defense-files"] }),
        invalidateAll: () => queryClient.invalidateQueries(),
    };
}
