<script>
const request = require('request');

const AWS_URL = 'https://rxaf4n42ye.execute-api.us-east-2.amazonaws.com/prod/'

const headers =  {
  'x-api-key': 'ca7nZ35PtD5lxNQQEW5rE5aP8416btyhce6RJPRa',
  'Content-Type': 'application/json'
};

export default {
  name: 'HelloWorld',
  data() {
      return {
        isBusy: true,
        loadingDirections: true,
        loadingAppts: true,        
        lastupdated: '',
        selectedLocation: {},
        tableData: [],
        fields: [
          {
            key: 'shortName',
            label: 'Name',
          },
          'address',
          {
            key: 'distance',
            sortable: true,
          },
          {
            key: 'utcTime',
            sortable: true,
            label: 'Earliest'
          },
          {
            key: 'vaccine',
            sortable: true
          },
        ]
      }
  },
  props: {},
  mounted () {
    const vue = this;
    
    request.get({
      'headers': headers,
      'url': AWS_URL + 'locations'
    }, (error, response) => {
      if (error) throw new Error(error);
      
      let locations = JSON.parse(response.body).locations;
      vue.tableData = locations;
      vue.isBusy = false;

      let now = new Date
      let time = now.toLocaleString().split(', ')[1].split(':')      
      vue.lastupdated = 'Today at ' + time[0]+':'+time[1]+' '+time[2].split(' ')[1].toLowerCase()
      
      let addresses = locations.map(x => ({
        mapsLocationString: x.mapsLocationString,
        id: x.id
      }));
      this.getDistances(addresses)

      let ids = locations.map(x => x.id);
      this.getAppts(ids)
    })
  },
  methods: {
    getDistances(addresses) {
      const vue = this;

      let body = { 
        addresses: addresses 
      }

      request.post({
        'headers': headers,
        'url': AWS_URL + 'distance',
        'body': body,
        'json': true
      }, (error, response) => {
        if (error) throw new Error(error);
        vue.loadingDirections = false;

        let distances = response.body.distances;

        for (let i=0; i<vue.tableData.length; i++) {
          let dist = distances.find(x => x.id === vue.tableData[i].id);
          vue.tableData[i].distance = dist.distance;
          vue.tableData[i].rawDistance = dist.rawDistance;
        }
        vue.$root.$emit('bv::refresh::table', 'data-table')
      });  
    },
    getAppts(ids) {
      const vue = this;

      let body = { 
        ids: ids 
      }

      request.post({
        'headers': headers,
        'url': AWS_URL + 'appointments',
        'body': body,
        'json': true
      }, (error, response) => {
        if (error) throw new Error(error);
        vue.loadingAppts = false;

        let appts = response.body.appts;

        for (let i=0; i<vue.tableData.length; i++) {
          let appt = appts.find(x => x.id === vue.tableData[i].id);
          vue.tableData[i].utcTime = appt.earliest.utcTime;
          vue.tableData[i].apptTime = appt.earliest.apptTime;
          vue.tableData[i].appts = appt.appts;
        }
        vue.$root.$emit('bv::refresh::table', 'data-table')
      }); 
    },
    openModal(id) {
      this.selectedLocation = this.tableData.find(x => x.id === id);
      if (this.selectedLocation.appts.length > 56) {
        this.selectedLocation.appts = this.selectedLocation.appts.slice(0,56)
        this.selectedLocation.appts.push({
          apptTime: 'more...',
          utcTime: '2022-01-01T00:00:00.000Z'
        })
      }
    }
  }
}
</script>
<template>
<div>
  <b-modal 
    ok-only 
    ok-variant="info"
    id="modal" 
    variant="info"
    :title="selectedLocation.shortName"
  >
    <ul class="d-flex flex-column flex-wrap">
      <li v-for="item in selectedLocation.appts" :key="item.utcTime">
        {{ item.apptTime }}
      </li>
    </ul>
  </b-modal>
  <div class="container">
    <h1>HRM Vaccine Appointments</h1>
    <p>Book online with a N.S Health card <a target="_blank" rel="noopener noreferrer" href="https://novascotia.flow.canimmunize.ca/en/9874123-19-7418965">here</a> or book by phone at <a href="tel:+1-833-797-7772">1-833-797-7772</a>.</p>
    <p>Last updated: {{lastupdated}}</p>
    <div class="d-flex justify-content-center mb-3" v-if="loadingDirections">
      <span class="mr-3">Getting Distances</span>
      <b-spinner label="Loading..."></b-spinner>
    </div>
    <div class="d-flex justify-content-center mb-3" v-if="loadingAppts">
      <span class="mr-3">Getting Appointment Times</span>
      <b-spinner label="Loading..."></b-spinner>
    </div>
    <div>
      <b-table 
        striped
        hover
        ref="table"
        id="data-table"
        :items="tableData"
        :fields="fields"
        :busy="isBusy"
        primary-key="id"
        sort-by="distance"
      >
        <template #cell(address)="data">
          <a :href="'https://www.google.com/maps/search/' + data.value.replace(/\s/g,'+')" target="_blank" rel="noopener noreferrer">{{ data.value }}</a>
        </template>
        <template #cell(utcTime)="data">
          <b-button 
            v-if="loadingAppts"
          >
            {{ data.item.apptTime }}
          </b-button> 
          <b-button 
            variant="info"
            v-if="!loadingAppts" 
            v-on:click="openModal(data.item.id)" 
            v-b-modal.modal
          >
            {{ data.item.apptTime }}
          </b-button> 
        </template>
      </b-table>
    </div>
  </div>
  <footer class="text-center">
    <p>Made with ❤️ by <a target="_blank" rel="noopener noreferrer" href="http://github.com/gwoods22/">Graeme Woods</a></p>
  </footer>
</div>
</template>
<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
button {
  min-width: 6rem;
}
ul {
  list-style-type: none;
  padding: 0;
  max-height: calc(100vh - 15rem);
}
li {
  display: inline-block;
  margin: 0 10px;
  width: fit-content;
}
td {
    text-align: left;
}
tr > td:first-child {
    width: 35%;
}
</style>
