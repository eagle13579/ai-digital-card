import React from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useAuth } from '../hooks/useAuth';

interface Props {
  onLogout?: () => void;
}

const ProfileScreen: React.FC<Props> = ({ onLogout }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    onLogout?.();
  };

  if (!user) {
    return (
      <View style={styles.center}>
        <Text style={styles.notLoggedIn}>未登录</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Avatar & basic info */}
      <View style={styles.header}>
        {user.avatar ? (
          <Image source={{ uri: user.avatar }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Text style={styles.avatarInitial}>
              {user.name.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
        <Text style={styles.name}>{user.name}</Text>
        <Text style={styles.email}>{user.email}</Text>
      </View>

      {/* Details */}
      <View style={styles.section}>
        {user.phone && (
          <View style={styles.row}>
            <Text style={styles.label}>电话</Text>
            <Text style={styles.value}>{user.phone}</Text>
          </View>
        )}
        {user.company && (
          <View style={styles.row}>
            <Text style={styles.label}>公司</Text>
            <Text style={styles.value}>{user.company}</Text>
          </View>
        )}
        {user.title && (
          <View style={styles.row}>
            <Text style={styles.label}>职位</Text>
            <Text style={styles.value}>{user.title}</Text>
          </View>
        )}
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>退出登录</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: '#fff',
    marginBottom: 12,
  },
  avatar: {
    width: 88,
    height: 88,
    borderRadius: 44,
    marginBottom: 12,
  },
  avatarPlaceholder: {
    backgroundColor: '#4a90d9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarInitial: {
    fontSize: 32,
    color: '#fff',
    fontWeight: '700',
  },
  name: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    color: '#888',
  },
  section: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#eee',
  },
  label: {
    fontSize: 16,
    color: '#888',
  },
  value: {
    fontSize: 16,
    color: '#333',
    maxWidth: '60%',
    textAlign: 'right',
  },
  logoutBtn: {
    marginHorizontal: 20,
    marginTop: 20,
    height: 48,
    backgroundColor: '#e53935',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoutText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  notLoggedIn: {
    fontSize: 16,
    color: '#999',
  },
});

export default ProfileScreen;
