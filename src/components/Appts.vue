<template>
    <div class="container">
      <h1>Vaccine Appointments</h1>
      <div>
        <b-table 
          striped
          hover
          :items="tableData"
          :fields="fields"
          :busy="isBusy"
          primary-key="id"
        ></b-table>
      </div>
    </div>
</template>

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
        tableData: [
          {
            appointmentTime: "2",
            address: "-",
            distance: "-",
            name: "-",
            id: 2
          },
          {
            appointmentTime: "1",
            address: "-",
            distance: "-",
            name: "-",
            id: 1
          }

        ],
        fields: [
          {
            key: 'shortName',
            sortable: false,
            label: 'Name'
          },
          {
            key: 'gisLocationString',
            sortable: false,
            label: 'Address'
          },
          {
            key: 'distance',
            sortable: false,
          },
          {
            key: 'vaccine',
            sortable: true
          },
        ]
      }
  },
  props: {
    msg: String
  },
  mounted () {
    const vue = this;
    
    request.get({
      'headers': headers,
      'url': AWS_URL + 'locations'
    }, function (error, response) {
      if (error) throw new Error(error);
      
      let locations = JSON.parse(response.body).locations;
      vue.tableData = locations;
      vue.isBusy = false;

      let addresses = locations.map(x => ({
        address: x.gisLocationString,
        id: x.id
      }));

      let body = { 
        addresses: addresses 
      }
      request.post({
        'headers': headers,
        'url': AWS_URL + 'distance',
        'body': body,
        'json': true
      }, function (error, response) {
        if (error) throw new Error(error);

        console.log(response.body);
        // let newData = vue.tableData;
        // for (let i=0; i<locations.length; i++) {
        //   newData.distance = newData.gisLocationString;
        // }
      });  
    })
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
